from spectate import mvc


class Counter(mvc.Model):
    def __init__(self):
        self.x = 0

    def increment(self, amount):
        self.x += amount

    def decrement(self, amount):
        self.x -= amount

    # define a control for incrementing and decrementing
    _control_change = mvc.Control("increment", "decrement")

    # register a beforeback to the control
    @_control_change.before
    def _control_change(self, call, notify):
        return self.x

    # register an afterback to the control
    @_control_change.after
    def _control_change(self, answer, notify):
        # Send an "event" dictionary to the Counter's views.
        notify(old=answer.before, new=self.x)


counter = Counter()


@mvc.view(counter)
def printer(event):
    print(event)


counter.increment(1)
counter.decrement(2)
counter.increment(3)
counter.decrement(4)
