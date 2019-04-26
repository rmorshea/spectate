def members(x):
    for k in dir(x):
        try:
            yield k, getattr(x, k)
        except AttributeError:
            pass


class Sentinel:
    def __init__(self, name):
        self.__name = name

    def __repr__(self):
        return self.__name
