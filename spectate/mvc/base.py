# See End Of File For Licensing
from inspect import signature
from functools import wraps
from typing import Union, Callable, Optional

from spectate.core import Watchable, watched, Data, MethodSpectator

from .utils import members


__all__ = ["Model", "Control", "view", "unview", "views"]


def views(model: "Model") -> list:
    """Return a model's views keyed on what events they respond to.

    Model views are added by calling :func:`view` on a model.
    """
    if not isinstance(model, Model):
        raise TypeError("Expected a Model, not %r." % model)
    return model._model_views[:]


def view(model: "Model", *functions: Callable) -> Optional[Callable]:
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
        raise TypeError("Expected a Model, not %r." % model)

    def setup(function: Callable):
        model._model_views.append(function)
        return function

    if functions:
        for f in functions:
            setup(f)
    else:
        return setup


def unview(model: "Model", function: Callable):
    """Remove a view callbcak from a model.

    Parameters:
        model: The model which contains the view function.
        function: The callable which was registered to the model as a view.

    Raises:
        ValueError: If the given ``function`` is not a view of the given ``model``.
    """
    model._model_views.remove(function)


class Control:
    """An object used to define control methods on a :class:`Model`

    A "control" method on a :class:`Model` is one which reacts to another method being
    called. For example there is a control method on the
    :class:`~spectate.mvc.models.List`
    which responds when :meth:`~spectate.mvc.models.List.append` is called.

    A control method is a slightly modified :ref:`beforeback <Spectator Beforebacks>` or
    :ref:`afterback <Spectator Afterbacks>` that accepts an extra ``notify`` argument.
    These are added to a control object by calling :meth:`Control.before` or
    :meth:`Control.after` respectively. The ``notify`` arugment is a function which
    allows a control method to send messages to :func:`views <view>` that are registered
    to a :class:`Model`.

    Parameters:
        methods:
            The names of the methods on the model which this control will react to
            When they are called.

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

    def __init__(self, *methods: str):
        self.methods = methods
        self.name = None

    def __get__(self, obj, cls):
        if obj is None:
            return self
        else:
            return BoundControl(obj, self)

    def before(self, callback: Union[Callable, str]) -> "Control":
        """Register a control method that reacts before the trigger method is called.

        Parameters:
            callback:
                The control method. If given as a callable, then that function will be
                used as the callback. If given as a string, then the control will look
                up a method with that name when reacting (useful when subclassing).
        """
        if isinstance(callback, Control):
            callback = callback._before
        self._before = callback
        return self

    def after(self, callback: Union[Callable, str]) -> "Control":
        """Register a control method that reacts after the trigger method is called.

        Parameters:
            callback:
                The control method. If given as a callable, then that function will be
                used as the callback. If given as a string, then the control will look
                up a method with that name when reacting (useful when subclassing).
        """
        if isinstance(callback, Control):
            callback = callback._after
        self._after = callback
        return self

    _after, _before = None, None

    def __set_name__(self, cls, name):
        if not issubclass(cls, Model):
            raise TypeError("Can only define a control on a Model, not %r" % cls)
        if self.name:
            msg = "Control was defined twice - %r and %r."
            raise RuntimeError(msg % (self.name, name))
        else:
            self.name = name
        for m in self.methods:
            setattr(cls, m, MethodSpectator(getattr(cls, m), m))


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
            events = []

            def notify(**event):
                events.append(Data(event))

            def parameters():
                meth = getattr(value, call.name)
                bound = signature(meth).bind(*call.args, **call.kwargs)
                return dict(bound.arguments)

            call = call["parameters":parameters]
            result = before(call, notify)
            if events:
                self._obj._notify_model_views(tuple(events))
            return result

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
            events = []

            def notify(**event):
                events.append(Data(event))

            result = after(answer, notify)
            if events:
                self._obj._notify_model_views(tuple(events))
            return result

        return afterback


class Model(Watchable):
    """An object that can be :class:`controlled <Control>` and :func:`viewed <view>`.

    Users should define :class:`Control` methods and then :func:`view` the change
    events those controls emit. This process starts by defining controls on a subclass
    of :class:`Model`.

    Examples:
        .. code-block:: python

            from specate import mvc

            class Object(mvc.Model):

                _control_attr_change = mvc.Control('__setattr__', '__delattr__')

                @_control_attr_change.before
                def _control_attr_change(self, call, notify):
                    return call.args[0], getattr(self, call.args[0], Undefined)

                @_control_attr_change.after
                def _control_attr_change(self, answer, notify):
                    attr, old = answer.before
                    new = getattr(self, attr, Undefined)
                    if new != old:
                        notify(attr=attr, old=old, new=new)

            o = Object()

            @mvc.view(o)
            def printer(o, events):
                for e in events:
                    print(e)

            o.a = 1
            o.b = 2

        .. code-block:: text

            {'attr': 'a', 'old': Undefined, 'new': 1}
            {'attr': 'b', 'old': Undefined, 'new': 2}
    """

    _model_controls = ()

    def __init_subclass__(cls, **kwargs):
        controls = []
        for k, v in members(cls):
            if isinstance(v, Control):
                controls.append(k)
        cls._model_controls = tuple(controls)
        super().__init_subclass__(**kwargs)

    def __new__(cls, *args, **kwargs):
        self, spectator = watched(super().__new__, cls)
        for name in cls._model_controls:
            ctrl = getattr(self, name)
            for method in ctrl.methods:
                spectator.callback(method, ctrl.before, ctrl.after)
        object.__setattr__(self, "_model_views", [])
        return self

    def _notify_model_views(self, events):
        for view in self._model_views:
            view(self, events)


# The MIT License (MIT)

# Copyright (c) 2016 Ryan S. Morshead

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
