import types
import inspect
from weakref import ref


# method wrapper source
_method_src = (
    """def {name}({signature}):
    __args__ = [{args}]
    for __val__ in ({defaults}):
        if not isinstance(__val__, __sentinel__):
            __args__.append(__val__)
    __args__.extend({varargs})
    __spectator__.instance_will_call('{name}', __args__, {keywords})
    try:
        result = __func__(*__args__, **{keywords})
    except Exception, e:
        __spectator__.error_raised(e)
    else:
        __spectator__.instance_post_call('{name}', result)
        return result
""")


class Sentinel(object):
    def __init__(self, obj):
        if isinstance(obj, (str, unicode)):
            self.name = obj
        else:
            self.name = repr(obj)
    def __repr__(self):
        return self.name


class Spectator(object):

    def __init__(self, inst):
        self.inst = inst
        self.names = []

    @property
    def inst(self):
        return self._inst()

    @inst.setter
    def inst(self, value):
        self._inst = ref(value)

    def instance_will_call(self, name, args, kwargs):
        pass

    def instance_post_call(self, name, returned):
        pass
    
    def error_raised(self, e):
        raise e


class method_spectator(object):

    _compile_count = 0

    def __init__(self, base, name):
        self.name = name
        self.base = base
        self.code = None

    def _gen_src_str(self, inst, func):
        if isinstance(func, types.FunctionType):
            aspec = inspect.getargspec(func)
        elif isinstance(func, types.MethodType):
            aspec = inspect.getargspec(func)
            # instance is provided by func
            del aspec.args[0]
        else:
            # no introspection is available for this type
            aspec = inspect.ArgSpec((), 'args', 'kwargs', ())

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
                sig += d + '=' + '__sentinel__(' + str(v) + ')' + ', '
        if aspec.varargs is not None:
            sig += '*' + aspec.varargs + ', '
        if aspec.keywords is not None:
            sig += '**' + aspec.keywords
        if sig[-2:] == ', ':
            sig = sig[:-2]

        a, kw = aspec.varargs or (), aspec.keywords or {}
        return _method_src.format(name=func.__name__, signature=sig,
            args=args, defaults=dvals, varargs=a, keywords=kw)

    def new_method(self, inst):
        func = getattr(self.base, self.name).__get__(inst)

        if self.code is None:
            src = self._gen_src_str(inst, func)
            filename = "traited-method-gen-%d" % self._compile_count
            try:
                code = compile(src, filename, 'single')
            except Exception, e:
                s = "Failed to compile - " + str(e)
                raise e.__class__(s)
            else:
                self._compile_count += 1

        evaldict = {'__sentinel__': Sentinel, '__func__': func,
                    '__spectator__': inst.instance_spectator}

        try:
            eval(code, evaldict)
        except Exception, e:
            s = "Failed to evaluate - " + str(e)
            raise e.__class__(s)

        newf = evaldict[func.__name__]
        newf.__doc__ = func.__doc__
        return newf

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
            inst.instance_spectator = spectator_type(inst)
            return inst

        classdict['__new__'] = __new__

        for name in notify_on:
            if not hasattr(base, name):
                raise ValueError("Cannot notify on '%s', because '%s' instances"
                                 " lack this method" % (name, base.__name__))
            else:
                classdict[name] = method_spectator(base, name)

        return super(WatchedType, mcls).__new__(mcls, name, (base,), classdict)

    def __init__(cls, name, base, spectator_type, *notify_on):
        pass
