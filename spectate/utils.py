from collections.abc import Mapping


class Sentinel:
    def __init__(self, name):
        self.__name = name

    def __repr__(self):
        return self.__name


class Immutable(Mapping):
    """An immutable mapping with attribute-access.

    Empty keys are represented with a value of ``None``.

    In order to evolve :class:`Immutable`, users must create copies that
    contain updates:

    .. code-block:: python

        d1 = Immutable(a=1)
        d2 = {'b': 1}
        assert Immutable(d1, **d2) == {'a': 1, 'b': 2}

    Easing this fact, is :class:`Immutable`'s syntactic sugar:

    .. code-block:: python

        d1 = Immutable(a=1) + {'b': 2}
        assert d1 == {'a': 1, 'b': 2}
    """

    def __init__(self, *args, **kwargs):
        self.__data = dict(*args, **kwargs)
        self.__keys = tuple(self.__data.keys())

    def __add__(self, other):
        return Immutable(self, **other)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        raise TypeError("%r is immutable")

    def __setattr__(self, key, value):
        if key.startswith("_%s" % type(self).__name__):
            super(Immutable, self).__setattr__(key, value)
        else:
            raise TypeError("%r is immutable")

    def __delitem__(self, key):
        raise TypeError("%r is immutable")

    def __delattr__(self, key):
        raise TypeError("%r is immutable")

    def __contains__(self, key):
        return key in tuple(self)

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __repr__(self):
        return repr(self.__data)

    def __hash__(self):
        return hash(tuple((k, self[k]) for k in self.__keys))
