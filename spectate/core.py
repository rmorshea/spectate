# See End Of File For Licensing

import sys
import inspect
import collections
from functools import wraps

try:
    from inspect import signature, Parameter, Signature
except ImportError:
    from funcsigs import signature, Parameter, Signature

__all__ = [
    "expose",
    "expose_as",
    "watch",
    "watched",
    "unwatch",
    "watcher",
    "watchable",
    "Watchable",
    "Data",
]


def _safe_signature(func):
    try:
        return signature(func)
    except ValueError:
        # builtin methods don't have sigantures
        return Signature(
            [
                Parameter("args", Parameter.VAR_POSITIONAL),
                Parameter("kwargs", Parameter.VAR_KEYWORD),
            ]
        )


def _signature_breakdown(func):
    args = []
    defaults = []
    var_keyword = None
    var_positional = None
    sig = _safe_signature(func)
    for param in sig.parameters.values():
        if param.kind == Parameter.VAR_POSITIONAL:
            var_positional = param.name
        elif param.kind == Parameter.VAR_KEYWORD:
            var_keyword = param.name
        else:
            if param.default is not Parameter.empty:
                defaults.append(param.default)
            args.append(param.name)
    return str(sig), tuple(args), defaults, var_positional, var_keyword


class Spectator(object):
    """An object for holding callbacks"""

    def __init__(self, subclass):
        """Create a Spectator that can be registered to a :class:`Watchable` instance.

        Parameters
        ----------
        subclass: type
            A the :class:`Watchable` subclass whose instance this
            :class:`Specatator` can respond to.
        """
        if not issubclass(subclass, Watchable):
            raise TypeError("Expected a Watchable, not %r." % subclass)
        self.subclass = subclass
        self._callback_registry = {}

    def callback(self, name, before=None, after=None):
        """Add a callback pair to this spectator.

        You can specify, with keywords, whether each callback should be triggered
        before, and/or or after a given method is called - hereafter refered to as
        "beforebacks" and "afterbacks" respectively.

        Parameters
        ----------
        name: str
            The name of the method to which callbacks should respond.
        before: None or callable
            A callable of the form ``before(obj, call)`` where ``obj`` is
            the instance which called a watched method, and ``call`` is a
            :class:`Data` containing the name of the called method, along with
            its positional and keyword arguments under the attributes "name"
            "args", and "kwargs" respectively.
        after: None or callable
            A callable of the form ``after(obj, answer)`` where ``obj` is
            the instance which alled a watched method, and ``answer`` is a
            :class:`Data` containing the name of the called method, along with
            the value it returned, and data ``before`` may have returned
            under the attributes "name", "value", and "before" respectively.
        """
        if isinstance(name, (list, tuple)):
            for name in name:
                self.callback(name, before, after)
        else:
            if not isinstance(getattr(self.subclass, name), MethodSpectator):
                raise ValueError("No method specator for '%s'" % name)
            if before is None and after is None:
                raise ValueError("No pre or post '%s' callbacks were given" % name)
            elif before is not None and not callable(before):
                raise ValueError("Expected a callable, not %r." % before)
            elif after is not None and not callable(after):
                raise ValueError("Expected a callable, not %r." % after)
            elif before is None and after is None:
                raise ValueError("No callbacks were given.")
            if name in self._callback_registry:
                callback_list = self._callback_registry[name]
            else:
                callback_list = []
                self._callback_registry[name] = callback_list
            callback_list.append((before, after))

    def remove_callback(self, name, before=None, after=None):
        """Remove a beforeback, and afterback pair from this Spectator

        If ``before`` and ``after`` are None then all callbacks for
        the given method will be removed. Otherwise, only the exact
        callback pair will be removed.

        Parameters
        ----------
        name: str
            The name of the method the callback pair is associated with.
        before: None or callable
            The beforeback that was originally registered to the given method.
        after: None or callable
            The afterback that was originally registered to the given method.
        """
        if isinstance(name, (list, tuple)):
            for name in name:
                self.remove_callback(name, before, after)
        elif before is None and after is None:
            del self._callback_registry[name]
        else:
            if name in self._callback_registry:
                callback_list = self._callback_registry[name]
            else:
                callback_list = []
                self._callback_registry[name] = callback_list
            callback_list.remove((before, after))
            if len(callback_list) == 0:
                # cleanup if all callbacks are gone
                del self._callback_registry[name]

    def call(self, obj, name, method, args, kwargs):
        """Trigger a method along with its beforebacks and afterbacks.

        Parameters
        ----------
        name: str
            The name of the method that will be called
        args: tuple
            The arguments that will be passed to the base method
        kwargs: dict
            The keyword args that will be passed to the base method
        """
        if name in self._callback_registry:
            beforebacks, afterbacks = zip(*self._callback_registry.get(name, []))

            hold = []
            for b in beforebacks:
                if b is not None:
                    call = Data(name=name, kwargs=kwargs.copy(), args=args)
                    v = b(obj, call)
                else:
                    v = None
                hold.append(v)

            out = method(*args, **kwargs)

            for a, bval in zip(afterbacks, hold):
                if a is not None:
                    a(obj, Data(before=bval, name=name, value=out))
                elif callable(bval):
                    # the beforeback's return value was an
                    # afterback that expects to be called
                    bval(out)
            return out
        else:
            return method(*args, **kwargs)


class MethodSpectator(object):
    """Notifies a :class:`Specator` when the method this descriptor wraps is called."""

    def __init__(self, basemethod, name):
        if not callable(basemethod):
            if isinstance(basemethod, MethodSpectator):
                basemethod = basemethod.basemethod
            else:
                raise TypeError("Expected a callable, not %r" % basemethod)
        self.basemethod = basemethod
        self.name = name

    def call(self, obj, cls):
        spectator = obj._instance_spectator

        if hasattr(self.basemethod, "__get__"):
            method = self.basemethod.__get__(obj, cls)
        else:
            method = self.basemethod

        @wraps(method)
        def wrapper(*args, **kwargs):
            return spectator.call(obj, self.name, method, args, kwargs)

        if not hasattr(wrapper, "__wrapped__"):
            wrapper.__wrapped__ = method
        return wrapper

    def __get__(self, obj, cls):
        if obj is None:
            return self
        elif hasattr(obj, "_instance_spectator"):
            return self.call(obj, cls)
        elif hasattr(self.basemethod, "__get__"):
            return self.basemethod.__get__(obj, cls)
        else:
            return self.basemethod


class Watchable(object):
    """A base class for introspection.

    And in Python>=3.6 rewraps overriden methods with a :class:`MethodSpectator`
    if appropriate.
    """

    if not sys.version_info < (3, 6):

        def __init_subclass__(cls, **kwargs):
            # If a subclass overrides a :class:`MethodSpectator` method, then rewrap it.
            for base in cls.mro()[1:]:
                if issubclass(base, Watchable):
                    for k, v in base.__dict__.items():
                        if k in cls.__dict__ and isinstance(v, MethodSpectator):
                            new = getattr(cls, k)
                            if callable(new) and not isinstance(new, MethodSpectator):
                                method_spectator = MethodSpectator(new, k)
                                setattr(cls, k, method_spectator)
            super().__init_subclass__(**kwargs)


def expose(*methods):
    """A decorator for exposing the methods of a class.

    Parameters
    ----------
    *methods : str
        A str representation of the methods that should be exposed to callbacks.

    Returns
    -------
    decorator : function
        A function accepting one argument - the class whose methods will be
        exposed - and which returns a new :class:`Watchable` that will
        notify a :class:`Spectator` when those methods are called.

    Notes
    -----
    This is essentially a decorator version of :func:`expose_as`
    """

    def setup(base):
        return expose_as(base.__name__, base, *methods)

    return setup


def expose_as(name, base, *methods):
    """Return a new type with certain methods that are exposed to callback registration.

    Parameters
    ----------
    name : str
        The name of the new type.
    base : type
        A type such as list or dict.
    *methods : str
        A str representation of the methods that should be exposed to callbacks.

    Returns
    -------
    exposed : obj:
        A :class:`Watchable` with methods that will notify a :class:`Spectator`.
    """
    classdict = {}
    for method in methods:
        if not hasattr(base, method):
            raise AttributeError(
                "Cannot expose '%s', because '%s' "
                "instances lack this method" % (method, base.__name__)
            )
        else:
            classdict[method] = MethodSpectator(getattr(base, method), method)
    return type(name, (base, Watchable), classdict)


def watchable(value):
    """Returns True if the given value is a :class:`Watchable` subclass or instance."""
    check = issubclass if inspect.isclass(value) else isinstance
    return check(value, Watchable)


def watch(value, spectator_type=Spectator):
    """Register a :class:`Specatator` to a :class:`Watchable` and return it.

    In order to register callbacks to an eventful object, you need to create
    a Spectator that will watch it for you. A :class:`Specatator` is a relatively simple
    object that has methods for adding, deleting, and triggering callbacks. To
    create a spectator we call ``spectator = watch(x)``, where x is a Watchable
    instance.

    Parameters
    ----------
    value : Watchable
        A :class:`Watchable` instance.
    spectator_type : Spectator
        The type of spectator that will be returned.

    Returns
    -------
    spectator: spectator_type
        The :class:`Specatator` (specified by ``spectator_type``) that is
        was registered to the given instance.
    """
    if isinstance(value, Watchable):
        wtype = type(value)
    else:
        raise TypeError("Expected a Watchable, not %r." % value)
    spectator = getattr(value, "_instance_spectator", None)
    if not isinstance(spectator, Spectator):
        spectator = spectator_type(wtype)
        value._instance_spectator = spectator
    return spectator


def watched(cls, *args, **kwargs):
    """Create and return a :class:`Watchable` with its :class:`Specatator`.

    See :func:`watch` for more info on :class:`Specatator` registration.

    Parameters
    ----------
    cls: type:
        A subclass of :class:`Watchable`
    *args:
        Positional arguments used to create the instance
    **kwargs:
        Keyword arguments used to create the instance.
    """
    value = cls(*args, **kwargs)
    return value, watch(value)


def unwatch(value):
    """Return the :class:`Specatator` of a :class:`Watchable` instance."""
    if not isinstance(value, Watchable):
        raise TypeError("Expected a Watchable, not %r." % value)
    spectator = watcher(value)
    try:
        del value._instance_spectator
    except Exception:
        pass
    return spectator


def watcher(value):
    """Return the :class:`Specatator` of a :class:`Watchable` instance."""
    if not isinstance(value, Watchable):
        raise TypeError("Expected a Watchable, not %r." % value)
    return getattr(value, "_instance_spectator", None)


class Data(collections.Mapping):
    """An immutable mapping with attribute-access.

    Empty keys are represented with a value of ``None``.

    In order to evolve :class:`Data`, users must create copies that
    contain updates:

    .. code-block:: python

        d1 = Data(a=1)
        d2 = Data(b=2)
        assert Data(d1, **d2) == {'a': 1, 'b': 2}

    Easing this fact, is :class:`Data`'s syntactic sugar:

    .. code-block:: python

        d1 = Data(a=1)
        assert d1 == {'a': 1}

        d2 = d1['b': 2]
        assert d2 == {'a': 1, 'b': 2}

        d3 = d2['a': None, 'b': 1]
        assert d3 == {'b': 1}

        d4 = d3[{'a': 1, 'c': 3}, {'b': None}]
        assert d4 == {'a': 1, 'c': 3}
    """

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __getattr__(self, key):
        return None

    def __getitem__(self, key):
        if type(key) is slice:
            key = (key,)
        if type(key) is tuple:
            for x in key:
                if not isinstance(x, slice):
                    break
            else:
                new = {s.start: s.stop for s in key}
                return type(self)(self, **new)
            merge = {}
            for x in key:
                if isinstance(x, collections.Mapping):
                    merge.update(x)
            key = merge
        if isinstance(key, collections.Mapping):
            return type(self)(self, **key)
        return self.__dict__.get(key)

    def __setitem__(self, key, value):
        raise TypeError("%r is immutable")

    def __setattr__(self, key, value):
        raise TypeError("%r is immutable")

    def __delitem__(self, key):
        raise TypeError("%r is immutable")

    def __delattr__(self, key):
        raise TypeError("%r is immutable")

    def __contains__(self, key):
        return key in tuple(self)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)


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
