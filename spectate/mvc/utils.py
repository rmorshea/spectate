import types
from weakref import proxy


class Sentinel:

    def __init__(self, name):
        self.__name = name

    def __repr__(self):
        return self.__name


class completemethod:

    _class_method = None
    _instance_method = None

    def __init__(self, function):
        self._class_method = function

    def __call__(self, function):
        self._instance_method = function
        return self

    def __set_name__(self, cls, name):
        if self._class_method is None:
            raise TypeError('No class method defined.')
        elif self._instance_method is None:
            raise TypeError('No instance method defined.')

    def __get__(self, obj, cls):
        if obj is None:
            return types.MethodType(self._class_method, cls)
        else:
            return types.MethodType(self._instance_method, obj)


def memory_safe_function(function):
    """Return a memory safe copy of a function.

    Through some clever tricks, all the defauts, and closure of this function
    are turned into proxy objects wherever possible. **Making a function memory
    safe may require its parent scope to be modified** - if the function contains
    a ``list``, ``dict``, or ``set`` in its closure or default arguments, all
    values contained in those data structures will be converted to proxy objects!

    Parameters
    ----------
    function: FunctionType, MethodType
        The function to be made into a memory safe copy.
    """
    if isinstance(function, types.MethodType):
        self = as_proxy(function.__self__)
        function = function.__func__
    elif not isinstance(function, types.FunctionType):
        raise TypeError('Expected a function or method, not %r.' % function)
    else:
        self = None

    closure = to_closure(as_proxy(cell.cell_contents) for cell in function.__closure__ or ())
    defaults = tuple(map(as_proxy, function.__defaults__ or ()))

    safe = types.FunctionType(
        function.__code__,
        function.__globals__,
        function.__name__,
        defaults,
        closure)

    if self is not None:
        safe = types.MethodType(safe, self)
    return safe


def as_proxy(x):
    if type(x) is list:
        for i, v in enumerate(x):
            x[i] = as_proxy(v)
        return x
    elif type(x) is dict:
        for k, v in x.items():
            x[as_proxy(k)] = as_proxy(v)
        return x
    elif type(x) is set:
        for v in x:
            x.remove(v)
            x.add(as_proxy(v))
        return x
    elif type(x) is tuple:
        return tuple(map(as_proxy, x))
    elif isinstance(x, (types.FunctionType, types.MethodType)):
        return memory_safe_function(x)
    else:
        try:
            return proxy(x)
        except TypeError:
            return x


def to_closure(args):
    args = list(args)
    if not args:
        return ()
    numbers = tuple(range(len(args)))
    outer = '\n    '.join(map('out{0} = var{0}'.format, numbers))
    inner = '\n        '.join(map('in{0} = out{0}'.format, numbers))
    form = 'def outer():\n    {0}\n    def inner():\n        {1}\n    return inner'

    variables = {'var%s' % i : x for i, x in enumerate(args)}
    source = form.format(outer, inner)

    exec(source, variables)

    return variables['outer']().__closure__


class _dict(dict):
    """Can be weakref"""
