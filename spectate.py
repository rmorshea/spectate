import types
import inspect
from weakref import ref

class Sentinel(object):
    def __init__(self, obj):
        if isinstance(obj, (str, unicode)):
            self.name = obj
        else:
            self.name = repr(obj)
    def __repr__(self):
        return self.name


_wrapper_src = """def {name}({signature}):
    try:
        __args = [{args}]
        for __val in ({defaults}):
            if not isinstance(__val, __sentinel):
                __args.append(__val)
        __args.extend({varargs})
        __spectator.instance_will_call('{name}', tuple(__args), {keywords}.copy())
        try:
            if __spectator.inst is None:
                raise ReferenceError('spectator has no instance')
            result = getattr(__spectator.base, '{name}').__get__(
                __spectator.inst, '{name}')(*__args, **{keywords})
        except Exception as e:
            __spectator.base_raised(e)
        else:
            __spectator.instance_post_call('{name}', result)
            return result
    except Exception as e:
        import sys
        tbo = sys.exc_info()[2]
        __spectator.wrap_raised(e,
            tbo.tb_frame.f_code.co_filename,
            tbo.tb_lineno)
"""

def RuntimeWrapperException(exc, filename, line):
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
    An error of the same type with the formated method, and a new
    attribute ``info`` containing the original exception, along with
    the name and line of the file in which is was raised.
    """
    inst = exc.__class__(str(exc) + ' @ ' + filename + '[lineno:%s]' % line)
    inst.info = (exc, filename, line)
    return inst


class Spectator(object):

    def __init__(self, base, inst):
        self.base = base
        self.inst = inst

    @property
    def inst(self):
        return self._inst()

    @inst.setter
    def inst(self, value):
        self._inst = ref(value)

    def instance_will_call(self, name, args, kwargs):
        """A callback made prior to calling the given base method

        Parameters
        ----------
        name: str
            The name of the method while will be called
        args: tuple
            The arguments that will be passed to the base method
        kwargs: dict
            A copy of the keywords args that will be passed to the base method
        """
        pass

    def instance_post_call(self, name, returned):
        """A callback made after calling the given base method

        Parameters
        ----------
        name: str
            The name of the method which was called.
        returned: any
            The value returned by the base method.

        Note
        ----
        Handle the returned value with care as this is ultimately
        what will be returned by the spectator's method wrapper."""
        pass

    def wrap_raised(self, exc, filename, line):
        """An error was raised by the method spectator's wrapper"""
        raise RuntimeWrapperException(exc, filename, line)
    
    def base_raised(self, e):
        """An error was raised while calling the base method"""
        raise e


class method_spectator(object):

    _wrapper_src = _wrapper_src

    _compile_count = 0

    def __init__(self, name):
        self.name = name
        self.code = None

    def _gen_src_str(self, func, reserved_names=None):
        """Creates an excecutable method wrapper string

        Parameters
        ----------
        func: the base method
            Attempts to extract the function signature. Defaults to
            ``(*args, **kwargs`` if introspection is unavailable.
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
            for name in reserved_names:
                if name in aspec.args or name in (a, kw):
                    raise ValueError(msg % name)

        split = len(aspec.args)-len(aspec.defaults)

        temp = str(aspec.args[:split])[1:-1]
        args = ''.join(temp.split("'"))

        sig = args + ', ' if args else ''

        defaults = aspec.args[split:]
        temp = str(defaults)[1:-1]
        if temp: temp += ','
        dvals = ''.join(temp.split("'"))

        if len(defaults) != 0:
            for d, v in zip(*(defaults, aspec.defaults)):
                sig += d + '=' + '__sentinel(' + str(v) + ')' + ', '
        if aspec.varargs is not None:
            sig += '*' + aspec.varargs + ', '
        if aspec.keywords is not None:
            sig += '**' + aspec.keywords
        if sig[-2:] == ', ':
            sig = sig[:-2]

        return self._wrapper_src.format(name=self.name, signature=sig,
            args=args, defaults=dvals, varargs=a or (), keywords=kw or {})

    def new_method(self, inst):
        """Returns a new method wrapper that notifies the instance's spectator"""
        evaldict = {'__spectator': inst.instance_spectator, '__sentinel': Sentinel}
        func = getattr(inst.instance_spectator.base, self.name)

        src = self._gen_src_str(func, evaldict.keys())
        self._eval_src(src, evaldict)

        # extract func and assign docs
        newf = evaldict[self.name]
        newf.__doc__ = func.__doc__
        return newf

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
            return self.new_method(inst)


class WatchedType(type):

    def __new__(mcls, name, base, spectator_type, notify_on):
        if isinstance(notify_on, (str, unicode)):
            notify_on = (notify_on,)

        classdict = base.__dict__.copy()

        def __new__(cls, *args, **kwargs):
            inst = base.__new__(cls, *args, **kwargs)
            inst.instance_spectator = spectator_type(base, inst)
            for name in notify_on:
                f = getattr(cls, name).new_method(inst)
                setattr(inst, name, f)
            return inst

        classdict['__new__'] = __new__

        for name in notify_on:
            if not hasattr(base, name):
                raise ValueError("Cannot notify on '%s', because '%s' instances"
                                 " lack this method" % (name, base.__name__))
            else:
                classdict[name] = method_spectator(name)

        return super(WatchedType, mcls).__new__(mcls, name, (base,), classdict)

    def __init__(cls, name, base, spectator_type, *notify_on):
        pass
