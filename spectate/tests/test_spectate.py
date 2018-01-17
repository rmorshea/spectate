import inspect
from ..spectate import (expose_as, watch, watched, watcher, unwatch,
    watchable, WatchableType, MethodSpectator, Spectator, Bunch)


def test_watchable():
    assert watchable(WatchableType)
    assert watchable(WatchableType())


def test_expose_as():
    WatchableList = expose_as("WatchableList", list, 'append')
    assert watchable(WatchableList)
    assert issubclass(WatchableList, list)
    assert WatchableList.__name__ == 'WatchableList'
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
    MethodSpectator._compile_count = 0
    WatchableList = expose_as("WatchableList", list, 'append')
    assert MethodSpectator._compile_count == 1
    append = WatchableList.append

    assert append.basemethod is list.append
    assert append.name == 'append'

    wl, spectator = watched(WatchableList)
    wl.append(1)
    wl.append(2)
    assert wl == [1, 2]


def test_method_spectator_argspec():
    WatchableThing = expose_as("WatchableThing", Thing, 'func')
    thing, sectator = watched(WatchableThing)
    assert MethodSpectator._compile_count == 2
    assert (inspect.getargspec(Thing().func) ==
        inspect.getargspec(thing.func))


def check_answer(checklist, inst, name, a, b, c=None, d=None, *e, **f):
    args, kwargs = condense(a, b, c, d, *e, **f)
    checklist.append(Bunch(
        name=name,
        value=(inst, a, b, c, d, e, f),
        before=Bunch(
            name=name,
            args=args,
            kwargs=kwargs))
    )
    getattr(inst, name)(a, b, c, d, *e, **f)


condense = lambda *a, **kw: (a, kw)


def test_beforeback_afterback():
    checklist = []

    WatchableThing = expose_as("WatchableThing", Thing, 'func')
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

    spectator.callback('func',
        before=beforeback, after=afterback)

    check_answer(checklist, wt, 'func', 1, 2, c=3)
    check_answer(checklist, wt, 'func', 1, 2, d=3)
    check_answer(checklist, wt, 'func', 1, 2, 3, 4, 5)
    check_answer(checklist, wt, 'func', 1, 2, d=3, f=4)
    assert callbacks_called == [4, 4]


def test_callback_closure():
    checklist = []

    WatchableThing = expose_as("WatchableThing", Thing, 'func')
    wt = WatchableThing()
    spectator = watch(wt)

    callbacks_called = [0, 0]

    def callback(inst, call):
        callbacks_called[0] += 1
        def closure(value):
            callbacks_called[1] += 1
            assert (checklist[-1] == Bunch(
                name=call.name, value=value,
                before=call))
        return closure

    spectator.callback('func', callback)

    check_answer(checklist, wt, 'func', 1, 2, c=3)
    check_answer(checklist, wt, 'func', 1, 2, d=3)
    check_answer(checklist, wt, 'func', 1, 2, 3, 4, 5)
    check_answer(checklist, wt, 'func', 1, 2, d=3, f=4)
    assert callbacks_called == [4, 4]


def test_callback_multiple():

    class Test(object):

        def a(self):
            pass

        def b(self):
            pass

    WatchableTest = expose_as("WatchableTest", Test, "a", "b")
    wt, spectator = watched(WatchableTest)

    callback = lambda value, call: None

    spectator.callback(("a", "b"), callback)

    for key in ("a", "b"):
        assert key in spectator._callback_registry
        assert spectator._callback_registry[key] == [(callback, None)]

    spectator.remove_callback(("a", "b"), callback)

    assert spectator._callback_registry == {}
