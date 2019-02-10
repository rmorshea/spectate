The Basics
==========

Spectate defines three main constructs:

1. :class:`models <spectate.mvc.base.Model>` - objects which get modified by the user.

2. :func:`views <spectate.mvc.base.view>` - functions which receives change events.

3. :class:`controls <spectate.mvc.base.Control>` - private attributes of a model which produces change events.

Since the :mod:`mvc <spectate.mvc>` module already provides some basic models for us you
don't need to worry about :class:`controls <spectate.mvc.base.Control>` yet. Let's begin
by considering a builtin :class:`~spectate.mvc.models.Dict` model. We can instantiate
this object just as we would with a standard :class:`dict`:

.. code-block:: python

    from spectate import mvc

    d = mvc.Dict(a=0)

Now though, we can now register a :func:`~spectate.mvc.base.view` function with a
decorator. This view function is called any time a change is made to the model ``d``
that causes its data to be mutated.

.. code-block:: python

    @mvc.view(d)  #  <--------- pass `d` in the decorator to observe its changes
    def printer(d, events):
        for e in events:  # <-- the view receives a tuple of immutable dict-like events
            print(e)

Change events are passed into this function as a tuple of immutable dict-like objects
containing change information. Each model has its own change event information.
In the case of a :class:`~spectate.mvc.models.Dict` the event objects have the fields
``key``, ``old``, and ``new``. So when we change a key in ``d`` we'll find that our
``printer`` view function is called and that it prints out an event object with the
expected information:

.. code-block:: python

    d["a"] = 1

.. code-block:: text

    {'key': 'a', 'old': 0, 'new': 1}

In cases where a mutation would result in changes to multiple change, one or more event
objects can be broadcast to the view function:

.. code-block:: python

    d.update(b=2, c=3)

.. code-block:: text

    {'key': 'b', 'old': Undefined, 'new': 2}
    {'key': 'c', 'old': Undefined, 'new': 3}
