from spectate import expose, watch


@expose("increment", "decrement")
class Counter(object):
    def __init__(self):
        self.x = 0

    def increment(self, amount):
        self.x += amount

    def decrement(self, amount):
        self.x -= amount


counter = Counter()
spectator = watch(counter)


def changed(counter, answer):
    print(counter.x)


spectator.callback("increment", after=changed)
spectator.callback("decrement", after=changed)

# see what happens when we modify the counter:

counter.increment(1)
counter.decrement(2)
counter.increment(3)
counter.decrement(4)
