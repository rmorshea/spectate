from spectate import expose, watch


@expose("__setattr__", "__delattr__")
class Immutable(object):
    def __init__(self):
        self._callbacks = []
        spectator = watch(self)
        spectator.callback("__setattr__", self._before_update, self._after_update)
        spectator.callback("__delattr__", self._before_update, self._after_update)

    @staticmethod
    def _before_update(data, call):
        key = call.args[0]
        old = data.__dict__.get(key)
        return key, old

    @staticmethod
    def _after_update(data, answer):
        key, old = answer.before
        new = data.__dict__.get(key)
        for c in data._callbacks:
            c(key=key, old=old, new=new)

    def watch(self, function):
        self._callbacks.append(function)
        return function


class User(Immutable):
    def __init__(self, name, description):
        super(User, self).__init__()
        self.name = name
        self.description = description


user = User("Paul", "a new user")


@user.watch
def printer(key, old, new):
    print("%s : %r -> %r" % (key, old, new))


user.name = "Paul Jones"
user.description = "updated user description"
