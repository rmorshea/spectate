class Sentinel:
    __slots__ = "_name"

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return self._name  # pragma: no cover
