import pytest

from spectate import mvc

from .mock import model_events, Counter


def test_hold_events():
    counter, events = model_events(Counter)

    with mvc.hold(counter) as cache:
        counter.increment(1)
        assert cache == [{"old": 0, "new": 1}]

        counter.increment(1)
        assert cache == [{"old": 0, "new": 1}, {"old": 1, "new": 2}]

        # Pop off one of the events so
        # it isn't sent to notifiers.
        cache.pop()

    assert events == [{"old": 0, "new": 1}]


def test_hold_uses_events_from_reducer():
    counter, events = model_events(Counter)

    def reducer(model, events):
        assert events == [{"old": 0, "new": 1}]
        yield {"custom": "event-1"}
        yield {"custom": "event-2"}

    with mvc.hold(counter, reducer=reducer):
        counter.increment(1)

    assert events == [{"custom": "event-1"}, {"custom": "event-2"}]


def test_rollback_events():
    counter, events = model_events(Counter)

    with pytest.raises(ValueError):
        with mvc.rollback(counter):
            counter.increment(1)
            raise ValueError()

    assert not events


def test_rollback_calls_undo_without_side_effects():
    calls = []
    counter, events = model_events(Counter)

    def undo(model, events, error):
        calls.append(1)
        assert error is error_from_rollback
        assert events == ({"old": 0, "new": 1},)
        # this decrement should not notify
        model.decrement(1)

    with pytest.raises(ValueError):
        with mvc.rollback(counter, undo=undo):
            counter.increment(1)
            error_from_rollback = ValueError()
            raise error_from_rollback

    assert calls
    assert counter.value == 0


def test_mute_events():
    counter, events = model_events(Counter)

    with mvc.mute(counter):
        counter.increment(1)
        counter.increment(1)

    assert events == []
