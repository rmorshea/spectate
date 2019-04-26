Creating Models
===============

Creating models requires you to define a :class:`~spectate.mvc.base.Model` subclass
which has :class:`~spectate.mvc.base.Control` objects assigned to it. Each control
object is responsible for observing calls to particular methods on the model class.
For example, if you wanted to know when an element was appended to a list you might
observe the ``append`` method.

To show how this works we will implement a simple counter with the goal of knowing when
the value in the counter has incremented or decremented. To get started we should create
a ``Counter`` class which inherits from :class:`~spectate.mvc.base.Model` and define
its ``increment`` and ``decrement`` methods normally:

.. code-block:: python

    from spectate import mvc

    class Counter(mvc.Model):

        def __init__(self):
            self.value = 0

        def increment(self, amount):
            self.value += amount

        def decrement(self, amount):
            self.value -= amount

.. code-block:: python

    c = Counter()
    c.increment(1)
    c.increment(1)
    c.decrement(1)
    assert c.value == 1


Adding Model Controls
---------------------

Because we know that the value within the ``Counter`` changes whenever ``increment`` or
``decrement`` is called these are the methods that we must observe in order to determine
whether, and by how much it changes. Do do this we should add a :class:`~spectate.mvc.base.Control`
to the ``Counter`` and pass in the names of the methods it should be tracking.

.. code-block:: python

    from spectate import mvc

    class Counter(mvc.Model):

        def __init__(self):
            self.value = 0

        def increment(self, amount):
            self.value += amount

        def decrement(self, amount):
            self.value -= amount

        _control_change = mvc.Control('increment', 'decrement')

We define the behavior of ``_control_change`` with methods that are triggered before
and/or after the ones being observed. We register these with
:meth:`Control.before() <~spectate.mvc.base.Control.before>`
and :meth:`Control.after() <~spectate.mvc.base.Control.after>`. For now our
beforeback and afterback will just contain print statements so we can see what they
receive when they are called.

.. code-block:: python

    from spectate import mvc

    class Counter(mvc.Model):

        def __init__(self):
            self.value = 0

        def increment(self, amount):
            self.value += amount

        def decrement(self, amount):
            self.value -= amount

        _control_change = (
            mvc.Control('increment', 'decrement')
            .before("_before_change")
            .after("_after_change")
        )

        def _before_change(self, call, notify):
            print("BEFORE")
            print(call)
            print(notify)
            print()
            return "result-from-before"

        def _after_change(self, answer, notify):
            print("AFTER")
            print(answer)
            print(notify)
            print()

No lets see what happens we can call ``increment`` or ``decrement``:

.. code-block:: python

    c = Counter()
    c.increment(1)
    c.decrement(1)

.. code-block:: text

    BEFORE
    {'name': 'increment', 'kwargs': {}, 'args': (1,), 'parameters': <function BoundControl.before.<locals>.beforeback.<locals>.parameters at 0x7f9ce57e8a60>}
    <function BoundControl.before.<locals>.beforeback.<locals>.notify at 0x7f9ce57e89d8>

    AFTER
    {'before': 'result-from-before', 'name': 'increment'}
    <function BoundControl.after.<locals>.afterback.<locals>.notify at 0x7f9ce57e89d8>

    BEFORE
    {'name': 'decrement', 'kwargs': {}, 'args': (1,), 'parameters': <function BoundControl.before.<locals>.beforeback.<locals>.parameters at 0x7f9ce57f2400>}
    <function BoundControl.before.<locals>.beforeback.<locals>.notify at 0x7f9ce57e89d8>

    AFTER
    {'before': 'result-from-before', 'name': 'decrement'}
    <function BoundControl.after.<locals>.afterback.<locals>.notify at 0x7f9ce57e89d8>


Model Callbacks
---------------

The callback pair we registered to our ``Counter`` when learning how to
:ref:`define controls <Adding Model Controls>`, hereafter referred to as
:ref:`"beforebacks" <Model Beforebacks>` and :ref:`"afterbacks" <Model Afterbacks>`
are how event information is communicated to views. Defining both a beforeback and
an afterback is not required, but doing so allows for a beforeback to pass data to its
corresponding afterback which in turn makes it possible to compute the difference
between the state before and the state after a change takes place:

.. code-block:: python

    from spectate import mvc

    class Counter(mvc.Model):

        def __init__(self):
            self.value = 0

        def increment(self, amount):
            self.value += amount

        def decrement(self, amount):
            self.value -= amount

        _control_change = (
            mvc.Control('increment', 'decrement')
            .before("_before_change")
            .after("_after_change")
        )

        def _before_change(self, call, notify):
            amount = call.parameters()["amount"]
            print("value will %s by %s" % (call.name, amount))
            old_value = self.value
            return old_value

        def _after_change(self, answer, notify):
            old_value = answer.before  # this was returned by `_before_change`
            new_value = self.value
            print("the old value was %r" % old_value)
            print("the new value is %r" % new_value)
            print("the value changed by %r" % (new_value - old_value))

Now we can try incrementing and decrementing as before:

.. code-block:: python

    c = Counter()
    c.increment(1)
    c.decrement(1)

.. code-block:: text

    value will increment by 1
    the old value was 0
    the new value is 1
    the value changed by 1
    value will decrement by 1
    the old value was 1
    the new value is 0
    the value changed by -1


Sending Event Notifications
---------------------------

We're now able to use :ref:`"beforebacks" <Model Beforebacks>` and
:ref:`"afterbacks" <Model Afterbacks>` to print out information about a model before
and after a change occures, but what we actually want is to send this same information to
:func:`views <spectate.mvc.base.view>` as we did when we learned :ref:`the basics`.
To accomplish this we use the ``notify`` function passed into the beforeback and
afterback and pass it keyword parameters that can be consumed by views. To keep
things simple we'll just replace our ``print`` statements with calls to ``notify``:

.. code-block:: python

    from spectate import mvc

    class Counter(mvc.Model):

        def __init__(self):
            self.value = 0

        def increment(self, amount):
            self.value += amount

        def decrement(self, amount):
            self.value -= amount

        _control_change = (
            mvc.Control('increment', 'decrement')
            .before("_before_change")
            .after("_after_change")
        )

        def _before_change(self, call, notify):
            amount = call.parameters()["amount"]
            notify(message="value will %s by %s" % (call.name, amount))
            old_value = self.value
            return old_value

        def _after_change(self, answer, notify):
            old_value = answer.before  # this was returned by `_before_change`
            new_value = self.value
            notify(message="the old value was %r" % old_value)
            notify(message="the new value is %r" % new_value)
            notify(message="the value changed by %r" % (new_value - old_value))

To print out the same messages as before we'll need to register a view with out counter:

.. code-block:: python

    c = Counter()

    @mvc.view(c)
    def print_messages(c, events):
        for e in events:
            print(e["message"])

    c.increment(1)
    c.decrement(1)

.. code-block:: text

    value will increment by 1
    the old value was 0
    the new value is 1
    the value changed by 1
    value will decrement by 1
    the old value was 1
    the new value is 0
    the value changed by -1


Model Beforebacks
-----------------

Have a signature of ``(call, notify) -> before``

+ ``call`` is a ``dict`` with the keys

    + ``'name'`` - the name of the method which was called

    + ``'args'`` - the arguments which that method will call

    + ``'kwargs'`` - the keywords which tCallbacks are registered to specific methods in
      pairs - one will be triggered before, and the other after, a call to that method
      is made. These two callbacks are referred to as "beforebacks" and "afterbacks"
      respectively. Defining both a beforeback and an afterback in each pair is not
      required, but doing so allows a beforeback to pass data to its corresponding
      afterback.

    + ``parameters`` a function which returns a dictionary where the ``args`` and ``kwargs``
      passed to the method have been mapped to argument names. This won't work for builtin
      method like :meth:`dict.get` since they're implemented in C.

+ ``notify`` is a function which will distribute an event to :func:`views <spectate.mvc.base.view>`

+ ``before`` is a value which gets passed on to its respective :ref:`afterback <Model Afterbacks>`.


Model Afterbacks
----------------

Have a signature of ``(answer, notify)``

+ ``answer`` is a ``dict`` with the keys

    + ``'name'`` - the name of the method which was called

    + ``'value'`` - the value returned by the method

    + ``'before'`` - the value returned by the respective beforeback

+ ``notify`` is a function which will distribute an event to :func:`views <spectate.mvc.base.view>`
