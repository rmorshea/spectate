import re
import types
import inspect
from weakref import ref

class WatchedType(object):
    """An eventful base class purely for introspection"""
    pass

class Sentinel(object):
    """A placeholder default value in _wrapper_src for introspection

    Any default value that is not set, i.e. the value is left as
    as a Sentinel instance, never gets passed to the base method.
    This means the base method will use a default value as, just
    like the user of the wrapper intended.

    Thus _wrapper_src, does not waste variable names trying to
    eval the true default value into the function signature.
    """
    def __init__(self, obj):
        if isinstance(obj, (str, unicode)):
            self.name = obj
        else:
            self.name = repr(obj)
    def __repr__(self):
        return self.name


class Bunch(dict):
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


_wrapper_src = """def {name}({signature}):
    __args = [{args}]
    for __val in ({defaults}):
        if not isinstance(__val, __sentinel):
            __args.append(__val)
    __args.extend({varargs})
    return __spectator.wrapper(__instance, '{name}',
        tuple(__args), {keywords}.copy())
"""

def source_wrapper_exception(exc, filename, lineno):
    """A factory for formating errors arising from wrapper source code

    Parameters
    ----------
    exc: Exception
        The exception instance raise by the wrapper
    filename: str
        The file the wrapper is defined in
    line: int
        The line number of the error

    Returns
    -------
    An error of the same type. with the formated method, and a new
    attribute ``info`` containing the original exception, along with
    the name and line of the file in which is was raised.
    """
    inst = exc.__class__(str(exc) + ' @ ' +
        filename + '[lineno:%s]' % lineno)
    return inst


class Spectator(object):

    def __init__(self, base, subclass):
        self.base = base
        self.subclass = subclass
        self._callback_registry = {}

    def register_callbacks(self, name, before=None, after=None, delete=False):
        if not isinstance(getattr(self.subclass, name), method_spectator):
            raise ValueError("No method specator for '%s'" % name)
        if before is None and after is None:
            raise ValueError("No pre or post '%s' callbacks were given" % name)
        elif ((before is not None and not callable(before))
            or (after is not None and not callable(after))):
            raise ValueError("Expected a callables")

        if name in self._callback_registry:
            l = self._callback_registry[name]
        else:
            l = []
            self._callback_registry[name] = l

        t = (before, after)
        if delete:
            try:
                l.remove(t)
            except:
                raise ValueError("The before and after pair %r does "
                    "not exist in the callback registry" % t)
        else:
            l.append(t)

    def wrapper(self, inst, name, args, kwargs):
        """A callback made prior to calling the given base method

        Parameters
        ----------
        inst: any
            The instance being spectated
        name: str
            The name of the method while will be called
        args: tuple
            The arguments that will be passed to the base method
        kwargs: dict
            A copy of the keywords args that will be passed to the base method
        """
        beforebacks, afterbacks = zip(*self._callback_registry.get(name, []))

        hold = []
        for b in beforebacks:
            if b is not None:
                try:
                    call = Bunch(name=name,
                        kwargs=kwargs.copy(),
                        args=args[1:])
                    v = b(inst, call)
                except Exception as e:
                    e = call
                else:
                    e = None
            else:
                v = None
                e = None
            hold.append(v)

        out = getattr(self.base, name)(*args, **kwargs)

        for a, bval in zip(afterbacks, hold):
            if a is not None:
                a(inst, Bunch(before=v,
                    name=name, value=out,
                    error=e))
        return out


class method_spectator(object):

    _compile_count = 0

    def __init__(self, name):
        self.code = None
        self.name = name

    def _gen_src_str(self, func, reserved_names=None):
        """Creates an excecutable method wrapper string

        Parameters
        ----------
        func: the base method
            Attempts to extract the function signature. Defaults to
            ``*args, **kwargs`` if introspection is unavailable.
        reserved_names: iterable
            A sequence of variables used internally by the source code.
            An error is raise if any of the reserved names are found
            in the base method's call signature.
        """
        if isinstance(func, types.FunctionType):
            aspec = inspect.getargspec(func)
        elif isinstance(func, types.MethodType):
            aspec = inspect.getargspec(func)
            # instance is provided by func
            del aspec.args[0]
        else:
            # no introspection is available for this type
            aspec = inspect.ArgSpec((), 'args', 'kwargs', ())

        a, kw = aspec.varargs, aspec.keywords

        if reserved_names:
            # see if argument names conflict with those
            # reserved by the wrapper source string
            msg = ("signature conflicts with reserved"
                    " name '%s' in new wrapper method")
            for name in list(reserved_names) + ["_"]:
                if name in aspec.args or name in a or name in kw:
                    raise ValueError(msg % name)

        # split point between defaults and normal args
        split = len(aspec.args or ()) - len(aspec.defaults or ())
        # remove tailing brackets from list conversion
        defaults = str(aspec.args[split:])[1:-1]
        args = str(aspec.args[:split])[1:-1]
        # list values were `repr`ed - remove "'"
        defaults = defaults.replace("'", "")
        args = args.replace("'", "")
        if len(defaults):
            defaults += ", "
        if len(args):
            args += ", "

        signature = args

        if len(defaults) != 0:
            for d, v in zip(*(defaults, aspec.defaults)):
                signature += d + '=' + '__sentinel(' + str(v) + ')' + ', '
        if aspec.varargs is not None:
            signature += '*' + aspec.varargs + ', '
        if aspec.keywords is not None:
            signature += '**' + aspec.keywords
        if signature.endswith(', '):
            signature = signature[:-2]

        return _wrapper_src.format(name=self.name, signature=signature,
            args=args, defaults=defaults, varargs=a or (), keywords=kw or {})

    def _eval_src(self, src, evaldict):
        """Evaluate the source string with the given eval dict.

        Compiled code is reused. Set ``self.code`` to ``None`` to reset.
        """
        if self.code is None:
            filename = "watched-method-gen-%d" % self._compile_count
            try:
                self.code = compile(src, filename, 'single')
            except Exception, e:
                s = "Failed to compile - " + str(e)
                raise e.__class__(s)
            else:
                self._compile_count += 1
        try:
            eval(self.code, evaldict)
        except Exception, e:
            s = "Failed to evaluate - " + str(e)
            raise e.__class__(s)

    def __get__(self, inst, cls):
        if inst is None:
            return self
        else:
            evaldict = {'__spectator': inst._instance_spectator,
                '__sentinel': Sentinel, '__instance': inst}
            func = getattr(inst._instance_spectator.base, self.name)

            src = self._gen_src_str(func, evaldict.keys())
            self._eval_src(src, evaldict)

            # extract func and assign docs
            newf = evaldict[self.name]
            newf.__doc__ = func.__doc__
            return types.MethodType(newf, inst)

def watched_type(name, base, *notify_on, **kwargs):
    classdict = base.__dict__.copy()
    classdict.update(kwargs.get('classdict', {}))

    def __new__(cls, *args, **kwargs):
        inst = base.__new__(cls, *args, **kwargs)
        object.__setattr__(inst, '_instance_spectator',
            kwargs.get('spectator_type', Spectator)(base, cls))
        return inst

    classdict['__new__'] = __new__

    def spectator_callback(self, *names, **callbacks):
        """Register a preemptive callback for method calls

        Parameters
        ----------
        **callbacks : callables
            The keys can be a near matches or 
        """
        for n in names:
            self._instance_spectator.register_callbacks(n, **callbacks)

    classdict['spectator_callback'] = spectator_callback

    for method in notify_on:
        if not hasattr(base, method):
            raise ValueError("Cannot notify on '%s', because '%s' "
                "instances lack this method" % (method, base.__name__))
        else:
            classdict[method] = method_spectator(method)

    return type(name, (base, WatchedType), classdict)
