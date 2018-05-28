import sys
from pytest import importorskip

# skips for python 3.6 or less
mvc = importorskip('spectate.mvc')


def test_mvc_custom_model():

    class Counter(mvc.Model):

        def __init__(self):
            self.x = 0

        def increment(self, amount):
            self.x += amount

        def decrement(self, amount):
            self.x -= amount

        # define a beforeback for increment and decrement
        @mvc.control.before('increment', 'decrement')
        def _control_change(self, call, notify):
            return self.x

        # create the corresponding afterback
        @_control_change.after
        def _control_change(self, answer, notify):
            # Send an "event" dictionary to the Counter's views.
            notify(old=answer.before, new=self.x)

    counter = Counter()
    events = []

    @mvc.view(counter)
    def printer(e):
        events.append(e)

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


def test_view_memory_safety():

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
