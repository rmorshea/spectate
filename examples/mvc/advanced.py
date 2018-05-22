from spectate import mvc


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


@mvc.view(counter)
def printer(event):
    print(event)


counter.increment(1)
counter.decrement(2)
counter.increment(3)
counter.decrement(4)
