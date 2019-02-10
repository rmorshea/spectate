Low Level Usage
===============

Expose any desired method of a class so it can be watched.

.. code-block:: python

    from spectate import expose, watch

    @expose('increment', 'decrement')
    class Counter(object):

        def __init__(self):
            self.value = 0

        def increment(self, amount):
            self.value += amount

        def decrement(self, amount):
            self.value -= amount

Create an instance of the new watchable class, and get its spectator.

.. code-block:: python

    counter = Counter()
    spectator = watch(counter)

Register a callback to the methods you exposed.

.. code-block:: python

    def changed(counter, answer):
        print(counter.value)

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


Spectator Callbacks
-------------------

Callbacks are registered to specific methods in pairs - one will be triggered before,
and the other after, a call to that method is made. These two callbacks are referred
to as "beforebacks" and "afterbacks" respectively. Defining both a beforeback and an
afterback in each pair is not required, but doing so allows a beforeback to pass data
to its corresponding afterback.


Spectator Beforebacks
'''''''''''''''''''''

Have a signature of ``(instance, call)``

+ ``instance`` is the owner of the method

+ ``call`` is a ``dict`` with the keys

  + ``'name'`` - the name of the method which was called

  + ``'args'`` - the arguments which that method will call

  + ``'kwargs'`` - the keywords which tCallbacks are registered to specific methods
    in pairs - one will be triggered before, and the other after, a call to that
    method is made. These two callbacks are referred to as "beforebacks" and
    "afterbacks" respectively. Defining both a beforeback and an afterback in each
    pair is not required, but doing so allows a beforeback to pass data to its
    corresponding afterback.

+ Can ``return`` a value which gets passed on to its respective afterback, or a
  `Beforeback Closures`_ that itself gets treated as an afterback.


Spectator Afterbacks
''''''''''''''''''''

Have a signature of ``(instance, answer)``

+ ``instance`` is the owner of the method
+ ``answer`` is a ``dict`` with the keys
  + ``'name'`` - the name of the method which was called
  + ``'value'`` - the value returned by the method
  + ``'before'`` - the value returned by the respective beforeback


Beforeback Closures
'''''''''''''''''''

Have a signature of ``(value)``

+ ``'value'`` - the value returned by the method
+ All other information is already contained in the closures scope.
+ Should not ``return`` anything.
