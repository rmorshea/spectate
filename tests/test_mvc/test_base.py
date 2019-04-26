from pytest import raises

from spectate.core import MethodSpectator
from spectate import mvc

from .mock import model_events, Counter


def test_control_is_only_for_model():
    """Controls must be defined on a Model"""
    with raises(RuntimeError):

        class X:
            _control = mvc.Control()


def test_control_decoration():

    calls = []

    class X(mvc.Model):
        def method(self):
            calls.append("during")

        control = mvc.Control("method")

        @control.before
        def control(self, call, notify):
            calls.append("before")

        @control.after
        def control(self, call, notify):
            calls.append("after")

    assert isinstance(X.method, MethodSpectator)

    X().method()
    assert calls == ["before", "during", "after"]


def test_control_string_reference():

    calls = []

    class X(mvc.Model):
        def method(self):
            pass

        control = mvc.Control("method").before("before").after("after")

        def before(self, call, notify):
            calls.append("before")

        def after(self, answer, notify):
            calls.append("after")

    X().method()
    assert calls == ["before", "after"]


def test_control_events_were_sent():
    counter, events = model_events(Counter)

    counter.increment(1)
    counter.decrement(2)
    counter.increment(3)
    counter.decrement(4)

    assert events == [
        {"old": 0, "new": 1},
        {"old": 1, "new": -1},
        {"old": -1, "new": 2},
        {"old": 2, "new": -2},
    ]


def test_override_control_methods_in_subclass():
    class MyCounter(Counter):
        def _control_before_change(self, call, notify):
            notify(message="before")
            return super()._control_before_change(call, notify)

    counter, events = model_events(MyCounter)

    counter.increment(1)

    assert events == [{"message": "before"}, {"old": 0, "new": 1}]


def test_add_new_control_in_subclass():
    class MyCounter(Counter):

        _added_control = mvc.Control("increment").before("_added_before")

        def _added_before(self, call, notify):
            notify(message="before")

    counter, events = model_events(MyCounter)

    counter.increment(1)

    assert events == [{"message": "before"}, {"old": 0, "new": 1}]


def test_delete_controls_in_subclass():
    class MyCounter(Counter):

        _control_change = None

    counter, events = model_events(MyCounter)

    counter.increment(1)

    assert events == []
