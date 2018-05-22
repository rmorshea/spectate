import types


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
