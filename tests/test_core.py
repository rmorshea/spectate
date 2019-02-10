import sys
from pytest import raises
from spectate.core import (
    expose,
    expose_as,
    watch,
    watched,
    watcher,
    unwatch,
    watchable,
    Watchable,
    MethodSpectator,
    Spectator,
    Data,
)

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


def test_watchable():
    assert watchable(Watchable)
    assert watchable(Watchable())


def test_expose():
    @expose("increment")
    class Counter(object):
        def __init__(self):
            self.x = 0

        def increment(self, amount=1):
            self.x += amount

    assert watchable(Counter)
    assert Counter.__name__ == "Counter"
    assert isinstance(Counter.increment, MethodSpectator)


def test_expose_as():
    WatchableList = expose_as("WatchableList", list, "append")
    assert watchable(WatchableList)
    assert issubclass(WatchableList, list)
    assert WatchableList.__name__ == "WatchableList"
    assert isinstance(WatchableList.append, MethodSpectator)


class Thing(object):
    def func(self, a, b, c=None, d=None, *e, **f):
        return (self, a, b, c, d, e, f)


def test_watch():
    WatchableThing = expose_as("WatchableThing", Thing, "func")
    wt = WatchableThing()
    spectator = watch(wt)

    assert isinstance(spectator, Spectator)
    assert hasattr(wt, "_instance_spectator")
    assert wt._instance_spectator is spectator

    WatchableList = expose_as("WatchableList", list, "append")
    wl, spectator = watched(WatchableList, [1, 2, 3])

    assert wl == [1, 2, 3]
    assert isinstance(spectator, Spectator)
    assert hasattr(wl, "_instance_spectator")
    assert wl._instance_spectator is spectator


def test_watched():
    WatchableThing = expose_as("WatchableThing", Thing, "func")
    wt, spectator = watched(WatchableThing)

    assert isinstance(spectator, Spectator)
    assert hasattr(wt, "_instance_spectator")
    assert wt._instance_spectator is spectator

    # Since watched uses watch under the hood
    # we don't need the remainder of the tests.


def test_watcher():
    WatchableThing = expose_as("WatchableThing", Thing, "func")
    wt, spectator = watched(WatchableThing)
    assert watcher(wt) is spectator


def test_unwatch():
    WatchableThing = expose_as("WatchableThing", Thing, "func")
    wt, spectator = watched(WatchableThing)
    out = unwatch(wt)
    assert not hasattr(wt, "_instance_spectator")
    assert out is spectator


def test_method_spectator():
    WatchableList = expose_as("WatchableList", list, "append")
    append = WatchableList.append

    assert append.basemethod is list.append
    assert append.name == "append"

    wl, spectator = watched(WatchableList)
    wl.append(1)
    wl.append(2)
    assert wl == [1, 2]


def test_method_spectator_signature():
    WatchableThing = expose_as("WatchableThing", Thing, "func")
    thing, sectator = watched(WatchableThing)
    assert signature(Thing().func) == signature(thing.func)


def check_answer(checklist, inst, name, a, b, c=None, d=None, *e, **f):
    args, kwargs = condense(a, b, c, d, *e, **f)
    checklist.append(
        Data(
            name=name,
            value=(inst, a, b, c, d, e, f),
            before=Data(name=name, args=args, kwargs=kwargs),
        )
    )
    getattr(inst, name)(a, b, c, d, *e, **f)


def condense(*a, **kw):
    return (a, kw)


def test_beforeback_afterback():
    checklist = []

    WatchableThing = expose_as("WatchableThing", Thing, "func")
    wt = WatchableThing()
    spectator = watch(wt)

    callbacks_called = [0, 0]

    # callback stores call information
    def beforeback(inst, call):
        callbacks_called[0] += 1
        return call

    def afterback(inst, answer):
        callbacks_called[1] += 1
        assert checklist[-1] == answer

    spectator.callback("func", before=beforeback, after=afterback)

    check_answer(checklist, wt, "func", 1, 2, c=3)
    check_answer(checklist, wt, "func", 1, 2, d=3)
    check_answer(checklist, wt, "func", 1, 2, 3, 4, 5)
    check_answer(checklist, wt, "func", 1, 2, d=3, f=4)
    assert callbacks_called == [4, 4]


def test_callback_closure():
    checklist = []

    WatchableThing = expose_as("WatchableThing", Thing, "func")
    wt = WatchableThing()
    spectator = watch(wt)

    callbacks_called = [0, 0]

    def callback(inst, call):
        callbacks_called[0] += 1

        def closure(value):
            callbacks_called[1] += 1
            assert checklist[-1] == Data(name=call.name, value=value, before=call)

        return closure

    spectator.callback("func", callback)

    check_answer(checklist, wt, "func", 1, 2, c=3)
    check_answer(checklist, wt, "func", 1, 2, d=3)
    check_answer(checklist, wt, "func", 1, 2, 3, 4, 5)
    check_answer(checklist, wt, "func", 1, 2, d=3, f=4)
    assert callbacks_called == [4, 4]


def test_callback_multiple():
    class Test(object):
        def a(self):
            pass

        def b(self):
            pass

    WatchableTest = expose_as("WatchableTest", Test, "a", "b")
    wt, spectator = watched(WatchableTest)

    def callback(value, call):
        pass

    spectator.callback(("a", "b"), callback)

    for key in ("a", "b"):
        assert key in spectator._callback_registry
        assert spectator._callback_registry[key] == [(callback, None)]

    spectator.remove_callback(("a", "b"), callback)

    assert spectator._callback_registry == {}


if not sys.version_info < (3, 6):

    def test_subclass_override():
        @expose("method")
        class Parent:
            def method(self):
                pass

        class Child(Parent):
            def method(self):
                pass

        assert watchable(Child)
        assert isinstance(Child.method, MethodSpectator)


def test_data_is_immutable():
    d = Data(a=0)
    with raises(TypeError):
        d["a"] = 1
    with raises(TypeError):
        d.a = 1
    with raises(TypeError):
        del d["a"]
    with raises(TypeError):
        del d.a
    assert d == {"a": 0}


def test_data_evolution():
    d0 = Data(a=0)
    d1 = d0["b":1]
    assert d1 == {"a": 0, "b": 1}
    d2 = d1["b":2, "c":3]
    assert d2 == {"a": 0, "b": 2, "c": 3}
    d3 = d2[{"b": 3, "c": 4}]
    assert d3 == {"a": 0, "b": 3, "c": 4}

    d0 = Data()
    d1 = d0[{"a": 1}, {"b": 2}]
    assert d1 == {"a": 1, "b": 2}


def test_data_is_mapping():
    assert dict(Data(a=0, b=1)) == {"a": 0, "b": 1}
    assert dict(**Data(a=0, b=1)) == {"a": 0, "b": 1}
