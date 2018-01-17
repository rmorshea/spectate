# See End Of File For Licensing


import re
import six
import types
import inspect


def getargspec(func):
    if isinstance(func, types.FunctionType) or isinstance(func, types.MethodType):
        return inspect.getargspec(func)
    else:
        # no signature introspection is available for this type
        return inspect.ArgSpec(None, 'args', 'kwargs', None)


class Bunch(dict):
    # Copyright (c) Jupyter Development Team.
    # Distributed under the terms of the Modified BSD License.

    """A dict with attribute-access"""
    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __dir__(self):
        # py2-compat: can't use super because dict doesn't have __dir__
        names = dir({})
        names.extend(self.keys())
        return names

    def copy(self):
        return Bunch(self)


class Spectator(object):

    def __init__(self, subclass):
        """Create a Spectator that can be registered to a ``WatchableType`` instance.
        
        Parameters
        ----------
        subclass: type
            A the ``WatchableType`` subclass whose instance this ``Spectator`` can respond to.
        """
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
            ``Bunch`` containing the name of the called method, along with
            its positional and keyword arguments under the attributes "name"
            "args", and "kwargs" respectively.
        after: None or callable
            A callable of the form ``after(obj, answer)`` where ``obj` is
            the instance which alled a watched method, and ``answer`` is a
            ``Bunch`` containing the name of the called method, along with
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
                l = self._callback_registry[name]
            else:
                l = []
                self._callback_registry[name] = l
            l.append((before, after))

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
                l = self._callback_registry[name]
            else:
                l = []
                self._callback_registry[name] = l
            l.remove((before, after))
            if len(l) == 0:
                # cleanup if all callbacks are gone
                del self._callback_registry[name]

    def wrapper(self, name, args, kwargs):
        """A callback made prior to calling the given base method
        
        The base method is retrieved from the ``WatchableType``
        subclass given in ``Spectator.__init__``.

        Parameters
        ----------
        name: str
            The name of the method that will be called
        args: tuple
            The arguments that will be passed to the base method
        kwargs: dict
            The keyword args that will be passed to the base method
        """
        ms = getattr(self.subclass, name)
        if not isinstance(ms, MethodSpectator):
            raise TypeError(
                "'%s.%s' has no MethodSpectator" % (
                self.subclass.__name__, name))
        if name in self._callback_registry:
            beforebacks, afterbacks = zip(*self._callback_registry.get(name, []))

            hold = []
            for b in beforebacks:
                if b is not None:
                    call = Bunch(name=name,
                        kwargs=kwargs.copy(),
                        args=args[1:])
                    v = b(args[0], call)
                else:
                    v = None
                hold.append(v)

            out = ms.basemethod(*args, **kwargs)

            for a, bval in zip(afterbacks, hold):
                if a is not None:
                    a(args[0], Bunch(before=bval,
                        name=name, value=out))
                elif callable(bval):
                    # the beforeback's return value was an
                    # afterback that expects to be called
                    bval(out)
            return out
        else:
            return ms.basemethod(*args, **kwargs)


class MethodSpectator(object):

    _compile_count = 0
    _src_str = """def {name}({signature}):
    args, vargs, kwargs = {args}, {varargs}, {keywords};
    return globals()["spectator"].wrapper('{name}', (args + vargs), kwargs)"""

    def __init__(self, base, name):
        self.name = name
        self.base = base
        aspec = getargspec(self.basemethod)
        self.defaults = aspec.defaults
        self.code, self.defaults = self._code(aspec)

    @property
    def basemethod(self):
        return getattr(self.base, self.name)

    def _code(self, aspec):
        args = str(aspec.args or ())[1:-1].replace("'", "")
        signature = args + (", " if aspec.args else "")
        if args:
            args = args.join(("(", ",)"))
        if aspec.varargs is not None:
            signature += '*' + aspec.varargs + ', '
        if aspec.keywords is not None:
            signature += '**' + aspec.keywords
        if signature.endswith(', '):
            signature = signature[:-2]

        src = self._src_str.format(name=self.name,
            signature=signature, args=args or (),
            varargs=aspec.varargs or (),
            keywords=aspec.keywords or {})
        name = re.findall('[A-Z][a-z]*', type(self).__name__)
        filename = "-".join(name).upper() + "-#%s"
        code = compile(src, filename % self._compile_count, 'single')
        type(self)._compile_count += 1
        return code, aspec.defaults

    def new_wrapper(self, inst, spectator):
        evaldict = {"spectator": spectator}
        eval(self.code, evaldict)
        # extract wrapper by name
        new = evaldict[self.name]
        # assign docstring and defaults
        new.__doc__ = self.basemethod.__doc__
        new.__defaults__ = self.defaults
        return types.MethodType(new, inst)

    def __get__(self, inst, cls):
        if inst is None:
            return self
        elif getattr(inst, "_instance_spectator", None):
            return self.new_wrapper(inst, inst._instance_spectator)
        else:
            return types.MethodType(self.basemethod, inst)


class WatchableType(object):
    """A base class for introspection."""
    pass


# TODO: Proofread doc string.
def expose_as(name, base, *methods):
    """Return a new type with certain methods that are exposed to callback registration.

    Parameters
    ----------
    name : str
        The name of the new type.
    base : type
        A type such as list or dict.
    methods : str
        A str representation of the methods that should be exposed to callbacks.

    Returns
    -------
    exposed : obj:
        A ``WatchableType`` with methods that will notify a ``Spectator``.
    """
    classdict = {}
    for method in methods:
        if not hasattr(base, method):
            raise AttributeError("Cannot expose '%s', because '%s' "
                "instances lack this method" % (method, base.__name__))
        else:
            classdict[method] = MethodSpectator(base, method)
    return type(name, (base, WatchableType), classdict)


# TODO: Proofread doc string.
def watchable(value):
    """Returns True if the given value is a subclass or instance of ``WatchableType``."""
    check = issubclass if inspect.isclass(value) else isinstance
    return check(value, WatchableType)


# TODO: Proofread doc string.
def watch(value, *args, **kwargs):
    """Register a ``Specatator`` to a ``WatchableType`` and return it.

    In order to register callbacks to an eventful object, you need to create
    a Spectator that will watch it for you. A ``Spectator`` is a relatively simple
    object that has methods for adding, deleting, and triggering callbacks. To
    create a spectator we call ``spectator = watch(x)``, where x is a WatchableType
    instance.

    Parameters
    ----------
    value : WatchableType
        A ``WatchableType`` instance.
    
    Returns
    -------
    spectator: Spectator
        The ``Spectator`` registered to the given instance.
    """
    if isinstance(value, WatchableType):
        wtype = type(value)
    else:
        raise TypeError("Expected a WatchableType, not %r." % value)
    spectator = getattr(value, "_instance_spectator", None)
    if not isinstance(spectator, Spectator):
        spectator = Spectator(wtype)
        value._instance_spectator = spectator
    return spectator


def watched(cls, *args, **kwargs):
    """Create and return a ``WatchableType`` with its ``Spectator``.
    
    See ``watch`` for more info on ``Spectator`` registration.
    
    Parameters
    ----------
    cls: type:
        A subclass of ``WatchableType``
    *args:
        Positional arguments used to create the instance
    **kwargs:
        Keyword arguments used to create the instance.
    """
    value = cls(*args, **kwargs)
    return value, watch(value)


def unwatch(value):
    """Return the ``Spectator`` of a ``WatchableType`` instance."""
    if not isinstance(value, WatchableType):
        raise TypeError("Expected a WatchableType, not %r." % value)
    spectator = watcher(value)
    try:
        del value._instance_spectator
    except:
        pass
    return spectator


def watcher(value):
    """Return the ``Spectator`` of a ``WatchableType`` instance."""
    if not isinstance(value, WatchableType):
        raise TypeError("Expected a WatchableType, not %r." % value)
    return getattr(value, "_instance_spectator", None)


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
