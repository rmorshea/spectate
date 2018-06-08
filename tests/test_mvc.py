import sys
from pytest import importorskip, fixture, raises

# skips for python 3.6 or less
mvc = importorskip('spectate.mvc')
from spectate.spectate import MethodSpectator


def model_events(mtype, *args, **kwargs):
    events = []
    model = mtype(*args, **kwargs)

    @mvc.view(model)
    def cache(e):
        events.extend(e)

    return model, events


class TestControl:

    def test_control_is_only_for_model(self):
        """Controls must be defined on a Model"""
        with raises(RuntimeError):
            class X:
                _control = mvc.Control()

    def test_control_decoration(self):

        calls = []

        class X(mvc.Model):

            def method(self):
                pass

            control = mvc.Control('method')

            @control.before
            def control(self, call, notify):
                calls.append('before')

            @control.after
            def control(self, call, notify):
                calls.append('after')

        assert isinstance(X.method, MethodSpectator)

        X().method()
        assert calls == ['before', 'after']


    def test_control_string_reference(self):

        calls = []

        class X(mvc.Model):

            def method(self): pass

            control = mvc.Control('method').before('before').after('after')

            def before(self, call, notify):
                calls.append('before')

            def after(self, answer, notify):
                calls.append('after')

        X().method()
        assert calls == ['before', 'after']


class TestView:

    class Counter(mvc.Model):

        def __init__(self):
            self.x = 0

        def increment(self, amount):
            self.x += amount

        def decrement(self, amount):
            self.x -= amount

        # define a beforeback for increment and decrement
        _control_change = mvc.Control('increment', 'decrement')

        @_control_change.before
        def _control_change(self, call, notify):
            return self.x

        # create the corresponding afterback
        @_control_change.after
        def _control_change(self, answer, notify):
            # Send an "event" dictionary to the Counter's views.
            notify(old=answer.before, new=self.x)

    def test_custom(self):
        counter, events = model_events(self.Counter)

        counter.increment(1)
        counter.decrement(2)
        counter.increment(3)
        counter.decrement(4)

        assert events == [
            {'old': 0, 'new': 1},
            {'old': 1, 'new': -1},
            {'old': -1, 'new': 2},
            {'old': 2, 'new': -2},
        ]

    def test_hold(self):
        counter, events = model_events(self.Counter)

        with mvc.hold(counter) as cache:
            counter.increment(1)
            assert cache == [
                {'old': 0, 'new': 1},
            ]

            counter.increment(1)
            assert cache == [
                {'old': 0, 'new': 1},
                {'old': 1, 'new': 2},
            ]

            # Pop off one of the events so
            # it isn't sent to notifiers.
            cache.pop()

        assert events == [
            {'old': 0, 'new': 1},
        ]

    def test_mute(self):
        counter, events = model_events(self.Counter)

        with mvc.mute(counter) as cache:
            counter.increment(1)
            counter.increment(1)

        assert events == []


def test_memory_safety():

    l = mvc.List()

    @mvc.view(l)
    def closure(event):
        # adds `l` to __closure__
        x = l

    @mvc.view(l)
    def defaults(event, l=l):
        # adds `l` to defaults
        x = l

    # Both of the above callbacks would normally create cirular
    # references, however mvc.utils.memory_safe_function will
    # mitigate this magically for the user.

    assert sys.getrefcount(l) == 2
