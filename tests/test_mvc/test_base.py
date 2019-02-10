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
