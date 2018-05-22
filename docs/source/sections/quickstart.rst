==========
Quickstart
==========

Expose any desired method of a class so it can be watched.

.. code-block:: python

    from spectate import expose, watch


    @expose('increment', 'decrement')
    class Counter(object):

        def __init__(self):
            self.x = 0

        def increment(self, amount):
            self.x += amount

        def decrement(self, amount):
            self.x -= amount

Create an instance of the new watchable class, and get its spectator.

.. code-block:: python

    counter = Counter()
    spectator = watch(counter)

Register a callback to the methods you exposed.

.. code-block:: python

    def changed(counter, answer):
        print(counter.x)

    spectator.callback('increment', after=changed)
    spectator.callback('decrement', after=changed)

Normal usage of the exposed methods will trigger your callback.

.. code-block:: python

    counter.increment(1)
    counter.decrement(2)
    counter.increment(3)
    counter.decrement(4)

And thus print out the following:

.. code-block:: text

    1
    -1
    2
    -2
