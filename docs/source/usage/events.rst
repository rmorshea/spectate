Handling Events
===============

Spectate provides a series of context managers which allow you to capture and then
modify events before they are distributed to views. This allows you to
:ref:`hold <Holding Events>`, :ref:`rollback <Rolling Back Events>`, and even
:ref:`mute <Muting Events>` events. These context managers are useful for handling
edge cases in your code, improving performance by :ref:`merging <Merging Events>`
events, or :ref:`undo <Rolling Back Changes>` unwanted changes.

Holding Events
--------------

It's often useful to withhold sending notifications until all your changes are complete.
Using the :func:`~spectate.events.hold` context manager, events created when
modifying a model won't be distributed until we exit the context:

.. code-block:: python

    d = mvc.Dict()

    # effectively the same as the printer view above
    mvc.view(d, lambda d, e: list(map(print, e)))

    print("before")
    with mvc.hold(d):
        d["a"] = 1
        print("during")
    # notifications are sent upon exiting
    print("after")

.. code-block:: text

    before
    during
    {'key': 'a', 'old': Undefined, 'new': 1}
    after


Merging Events
''''''''''''''

Sometimes there is a block of code in which it's possible to produce duplicate events
or events which could be merged into one. By passing in a ``reducer`` to
:func:`~spectate.events.hold` you can change the list of events just before they
are distributed. This is done by having the ``reducer`` return or yield the new events.

.. code-block:: python

    from spectate import mvc

    d = mvc.Dict()

    mvc.view(d, lambda _, es: list(map(print, es)))

    def merge_dict_events(model, events):
        changes = {}

        for e in events:
            if e.key in changes:
                changes[e.key][1] = e.new
            else:
                changes[e.key] = [e.old, e.new]

        for key, (old, new) in changes.items():
            yield {"key": key, "new": new, "old": old}

    with mvc.hold(d, reducer=merge_dict_events):
        for i in range(5):
            # this loop would normally produce 5 different events
            d["a"] = i

.. code-block:: text

    {'key': 'a', 'new': Undefined, 'old': 4}


Rolling Back Events
-------------------

When an error occurs while modifying a model you may not want to distribute events.
Using :func:`~spectate.events.rollback` you can suppress events that were produced
in the same context as an error:

.. code-block:: python

    from spectate import mvc

    d = mvc.Dict()

    @mvc.view(d)
    def should_not_be_called(d, events):
        # we never call this view
        assert False

    try:
        with mvc.rollback(d):
            d["a"] = 1
            d["b"]  # key doesn't exist
    except KeyError:
        pass


Rolling Back Changes
''''''''''''''''''''

Suppressing events after an error may not be enough. You can pass :func:`~spectate.events.rollback`
an ``undo`` function which gives you a chances to analyze the events in order to determine
and then return a model to its original state. Any events that you might produce while
modifying a model within the ``undo`` function will be :ref:`muted <Muting Events>`.

.. code-block:: python

    d = mvc.Dict()

    def undo_dict_changes(model, events, error):
        seen = set()
        for e in reversed(events):
            if e.old is mvc.Undefined:
                del model[e.key]
            else:
                model[e.key] = e.old

    try:
        with mvc.rollback(d, undo=undo_dict_changes):
            d["a"] = 1
            d["b"] = 2
            print(d)
            d["c"]
    except KeyError:
        pass
    print(d)

.. code-block:: text

    {'a': 1, 'b': 2}
    {}


Muting Events
-------------

If you are setting a default state, or returning to one, it may be useful to withhold
events completely. This one's pretty simple compared to the context managers above.
Just use :func:`~spectate.events.mute` and within its context, no events will
be distributed:

.. code-block:: python

    from spectate import mvc

    l = mvc.List()

    @mvc.view(l)
    def raises(events):
        # this won't ever happen
        raise ValueError("Events occured!")

    with mvc.mute(l):
        l.append(1)


Force Notifying
---------------

At times, and more likely when writing tests, you may need to forcefully send an event
to a model. This can be achieved using the :func:`~spectate.base.notifier` context
manager which provides a ``notify()`` function identical to the one seen in
:ref:`Model Callbacks`.

.. warning::

    While you could use :func:`~spectate.base.notifier` instead of adding
    :ref:`Adding Model Controls` to your custom models, this is generall discouraged
    because the resulting implementation is resistent to extension in subclasses.

.. code-block:: python

    from spectate import mvc

    m = mvc.Model()

    @mvc.view(m)
    def printer(m, events):
        for e in events:
            print(e)

    with mvc.notifier(m) as notify:
        # the view should print out this event
        notify(x=1, y=2)
