from inspect import signature
from functools import wraps
from typing import (
    Any,
    Union,
    Callable,
    Optional,
    TypeVar,
    Tuple,
    Dict,
    List,
    Iterator,
    overload,
)
from contextlib import contextmanager
from weakref import WeakValueDictionary


__all__ = ["Model", "Control", "view", "unview", "views", "link", "unlink", "notifier"]

Event = Dict[str, Any]
TupleOfEvents = Tuple[Event, ...]
ViewFunction = Callable[["Model", TupleOfEvents], None]


def views(model: "Model") -> List[ViewFunction]:
    """Return a model's views keyed on what events they respond to.

    Model views are added by calling :func:`view` on a model.
    """
    if not isinstance(model, Model):
        raise TypeError("Expected a Model, not %r." % model)
    return model._model_views[:]


_F = TypeVar("_F", bound=ViewFunction)


@overload
def view(model: "Model") -> Callable[[_F], _F]:
    ...


@overload
def view(model: "Model", function: ViewFunction) -> None:
    ...


def view(
    model: "Model", function: Optional[ViewFunction] = None
) -> Optional[Callable[[_F], _F]]:
    """A decorator for registering a callback to a model

    Parameters:
        model: the model object whose changes the callback should respond to.

    Examples:
        .. code-block:: python

            from spectate import mvc

            items = mvc.List()

            @mvc.view(items)
            def printer(items, events):
                for e in events:
                    print(e)

            items.append(1)
    """
    if not isinstance(model, Model):
        raise TypeError("Expected a Model, notself._model_notifier() %r." % model)

    def setup(function: _F) -> _F:
        model._attach_model_view(function)
        return function

    if function is not None:
        setup(function)
        return None
    else:
        return setup


def unview(model: "Model", function: ViewFunction) -> None:
    """Remove a view callbcak from a model.

    Parameters:
        model: The model which contains the view function.
        function: The callable which was registered to the model as a view.

    Raises:
        ValueError: If the given ``function`` is not a view of the given ``model``.
    """
    model._remove_model_view(function)


def link(source: "Model", *targets: "Model") -> None:
    """Attach all of the source's present and future view functions to the targets.

    Parameters:
        source: The model whose view functions will be attached to the targets.
        targets: The models that will acquire the source's view functions.
    """
    for t in targets:
        source._attach_child_model(t)


def unlink(source: "Model", *targets: "Model") -> None:
    """Remove all of the source's present and future view functions from the targets.

    Parameters:
        source: The model whose view functions will be removed from the targets.
        targets: The models that will no longer share view functions with the source.
    """
    for t in targets:
        source._remove_child_model(t)


@contextmanager
def notifier(model: "Model") -> Iterator[Callable[..., None]]:
    """Manually send notifications to the given model.

    Parameters:
        model: The model whose views will recieve notifications

    Returns:
        A function whose keyword arguments become event data.

    Example:

        .. code-block:: python

            m = Model()

            @view(m)
            def printer(m, events):
                for e in events:
                    print(e)

            with notifier(m) as notify:
                # the view should print out this event
                notify(x=1, y=2)
    """
    events = []

    def notify(*args, **kwargs):
        events.append(dict(*args, **kwargs))

    yield notify

    if events:
        model._notify_model_views(tuple(events))


class Control:
    """An object used to define control methods on a :class:`Model`

    A "control" method on a :class:`Model` is one which reacts to another method being
    called. For example there is a control method on the
    :class:`~spectate.mvc.models.List`
    which responds when :meth:`~spectate.mvc.models.List.append` is called.

    A control method is a slightly modified :ref:`beforeback <Control Beforebacks>` or
    :ref:`afterback <Control Afterbacks>` that accepts an extra ``notify`` argument.
    These are added to a control object by calling :meth:`Control.before` or
    :meth:`Control.after` respectively. The ``notify`` arugment is a function which
    allows a control method to send messages to :func:`views <view>` that are registered
    to a :class:`Model`.

    Parameters:
        methods:
            The names of the methods on the model which this control will react to
            When they are calthrough the Nodeled. This is either a comma seperated
            string, or a list of strings.
        before:
            A control method that reacts before any of the given ``methods`` are
            called. If given as a callable, then that function will be used as the
            callback. If given as a string, then the control will look up a method
            with that name when reacting (useful when subclassing).
        after:
            A control method that reacts after any of the given ``methods`` are
            alled. If given as a callable, then that function will be used as the
            callback. If given as a string, then the control will look up a method
            with that name when reacting (useful when subclassing).

    Examples:
        Control methods are registered to a :class:`Control` with a ``str`` or function.
        A string may refer to the name of a method on a `Model` while a function should
        be decorated under the same name as the :class:`Control` object to preserve the
        namespace.

        .. code-block:: python

            from spectate import mvc

            class X(mvc.Model):

                _control_method = mvc.Control("method").before("_control_before_method")

                def _control_before_method(self, call, notify):
                    print("before")

                # Note how the method uses the same name. It
                # would be redundant to use a different one.
                @_control_a.after
                def _control_method(self, answer, notify):
                    print("after")

                def method(self):
                    print("during")

            x = X()
            x.method()

        .. code-block:: text

            before
            during
            after
    """

    def __init__(
        self,
        methods: Union[list, tuple, str],
        *,
        before: Union[Callable, str] = None,
        after: Union[Callable, str] = None,
    ):
        if isinstance(methods, (list, tuple)):
            self.methods = tuple(methods)
        elif isinstance(methods, str):
            self.methods = tuple(map(str.strip, methods.split(",")))
        else:
            raise ValueError("methods must be a string or list of strings")
        self.name = None
        if isinstance(before, Control):
            before = before._before
        self._before = before
        if isinstance(after, Control):
            after = after._after
        self._after = after

    def __get__(self, obj, cls):
        if obj is None:
            return self
        else:
            return BoundControl(obj, self)

    def __set_name__(self, cls, name):
        if not issubclass(cls, Model):
            raise TypeError("Can only define a control on a Model, not %r" % cls)
        if self.name:
            msg = "Control was defined twice - %r and %r."
            raise RuntimeError(msg % (self.name, name))
        else:
            self.name = name
        for m in self.methods:
            setattr(cls, m, self._create_controlled_method(cls, m))

    def _create_controlled_method(self, cls, name):
        method = getattr(cls, name)

        @wraps(method)
        def wrapped_method(obj, *args, **kwargs):
            cls = type(obj)
            bound_control = self.__get__(obj, cls)

            before_control = bound_control.before
            if before_control is not None:
                before_value = before_control(
                    obj, {"name": name, "args": args, "kwargs": kwargs}
                )
            else:
                before_value = None

            result = method.__get__(obj, cls)(*args, **kwargs)

            after_control = bound_control.after
            if after_control is not None:
                after_control(
                    obj, {"before": before_value, "name": name, "value": result}
                )

            return result

        return wrapped_method


class BoundControl:
    def __init__(self, obj, ctrl):
        self._obj = obj
        self._cls = type(obj)
        self._name = ctrl.name
        self._before = ctrl._before
        self._after = ctrl._after
        self.methods = ctrl.methods

    @property
    def before(self):
        if self._before is None:
            method_name = self._name + "_before"
            if hasattr(self._obj, method_name):
                before = getattr(self._obj, method_name)
            else:
                return None
        else:
            before = self._before

        if isinstance(before, str):
            before = getattr(self._obj, before)
        elif hasattr(before, "__get__"):
            before = before.__get__(self._obj, type(self._obj))

        @wraps(before)
        def beforeback(value, call):
            def parameters():
                meth = getattr(value, call["name"])
                bound = signature(meth).bind(*call["args"], **call["kwargs"])
                return dict(bound.arguments)

            with notifier(value) as notify:
                return before(dict(call, parameters=parameters), notify)

        return beforeback

    @property
    def after(self):
        if self._after is None:
            return None
        else:
            after = self._after

        if isinstance(after, str):
            after = getattr(self._obj, after)
        elif hasattr(after, "__get__"):
            after = after.__get__(self._obj, type(self._obj))

        @wraps(after)
        def afterback(value, answer):
            with notifier(value) as notify:
                return after(answer, notify)

        return afterback


class Model:
    """An object that can be :class:`controlled <Control>` and :func:`viewed <view>`.

    Users should define :class:`Control` methods and then :func:`view` the change
    events those controls emit. This process starts by defining controls on a subclass
    of :class:`Model`.

    Examples:
        .. code-block:: python

            from specate import mvc

            class Object(Model):

                _control_attr_change = Control(
                    "__setattr__, __delattr__",
                    before="_control_before_attr_change",
                    after="_control_after_attr_change",
                )

                def __init__(self, *args, **kwargs):
                    for k, v in dict(*args, **kwargs).items():
                        setattr(self, k, v)

                def _control_before_attr_change(self, call, notify):
                    return call["args"][0], getattr(self, call["args"][0], Undefined)

                def _control_after_attr_change(self, answer, notify):
                    attr, old = answer["before"]
                    new = getattr(self, attr, Undefined)
                    if new != old:
                        notify(attr=attr, old=old, new=new)

            o = Object()

            @mvc.view(o)
            def printer(o, events):
                for e in events:
                    print(e)
    """

    _model_views: List[ViewFunction]
    _inner_models: "WeakValueDictionary[int, Model]"

    def __new__(cls, *args: Any, **kwargs: Any) -> "Model":
        new = super().__new__
        if new is not object.__new__:
            self = new(cls, *args, **kwargs)  # type: ignore
        else:
            self = new(cls)

        object.__setattr__(self, "_model_views", [])
        object.__setattr__(self, "_inner_models", WeakValueDictionary())

        return self

    def _attach_child_model(self, model: "Model") -> None:
        self._inner_models[id(model)] = model
        for v in self._model_views:
            model._attach_model_view(v)

    def _remove_child_model(self, model: "Model") -> None:
        try:
            del self._inner_models[id(model)]
        except KeyError:
            pass
        else:
            for v in self._model_views:
                model._remove_model_view(v)

    def _attach_model_view(self, function: ViewFunction) -> None:
        self._model_views.append(function)
        for inner in self._inner_models.values():
            inner._attach_model_view(function)

    def _remove_model_view(self, function: ViewFunction) -> None:
        self._model_views.remove(function)
        for inner in self._inner_models.values():
            inner._remove_model_view(function)

    def _notify_model_views(self, events: TupleOfEvents):
        for view in self._model_views:
            view(self, events)
