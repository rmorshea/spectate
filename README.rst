========
Spectate
========
Create classes whose instances have tracked methods

Instalation
-----------
``spectate`` can be installed from GitHub using ``pip``:

.. code:: text
    
    $ pip install git+https://github.com/rmorshea/spectate.git#egg=spectate

Basic Usage
-----------
``spectate`` is useful for remotely tracking how an instance is modified. This means that protocols
for managing updates, don't need to be the outward responsibility of a user, and can instead be
done automagically in the background.

For example, if it were desirable to keep track of element changes in a list, ``spectate`` could be
used to observe ``list.__setitiem__`` in order to be notified when a user sets the value of an element
in the list. To do this, we would first create a ``EventfulList`` using ``watched_type``, and then
store pairs of callbacks to an instance of ``EventfulList`` using its `instance_spectator` attribute.
Each pair is registered by calling the `instance_spectator`'s `callback` method. You can then specify,
with keywords, whether the callback should be triggered ``before``, and/or or ``after`` a given method
is called - hereafter refered to as "beforebacks" and "afterbacks" respectively.

Beforebacks
-----------

+ Have a signature of ``(instance, call)``

+   ``instance`` is the owner of the method

    +   ``call`` is a ``Bunch`` with the keys:

        + ``'name'`` - the name of the method which was called
        + ``'args'`` - the arguments which that method will call
        + ``'kwargs'`` - the keywords which that method will call

+   Can ``return`` a value which gets passed on to its respective afterback.
+   If an error is encountered:

    +   The wrapper will:

        1. ``return`` the original ``call``
        2. Set the ``'error'`` key in the ``answer`` passed to its afterback.

    +   The base method's call is not obstructed by raised beforebacks.

Afterbacks
----------

+   Have a signature of ``(instance, answer)``

    +   ``instance`` is the owner of the method
    +   ``answer`` is a ``Bunch`` with the keys:

        +   ``'name'`` - the name of the method which was called
        +   ``'value'`` - the value returned by the method
        +   ``'before'`` - the value returned by the respective beforeback

+ Should not ``return``

Example
-------

.. code-block:: python

    from spectate import watched_type

    EventfulList = watched_type('EventfulList', list, '__setitem__')

    def pass_on_old_value(inst, call):
        """The beforeback"""
        index = call.args[0]
        old = inst[index]
        return index, old

    def print_element_change(inst, answer):
        """The afterback"""
        # answer.before = pass_on_old_value(call)
        index, old = answer.before
        new = inst[index]
        if new != old:
            print("{%s: %s} -> {%s: %s}" %
                (index, old, index, new))

``pass_on_old_value`` simply pulls the old value stored at the given index, and then passes
that value and the index on to its afterback. The afterback then checks to see if the value
which is `now` stored at that index, is equal to the value which `was` stored there. If it is,
nothing happens, however if it isn't, the change gets printed.

Instances of ``EventfulList`` will behave exactly like a ``list`` in every way. The only
difference being that when a user decides to change the value of a preexisting element, the
spectator is notified, and will print once the action is complete:

.. code-block:: python

    elist = EventfulList([1, 2, 3])

    elist.instance_spectator.callback('__setitem__',
        before=pass_on_old_value,
        after=print_element_change)

    elist[0] = 0

Prints ``{0: 1} -> {0: 0}``

Under The Hood
--------------
Methods are tracked by using ``watched_type`` to create a new class with ``MethodSpectator`` descriptors in
the place of specified methods. At the time an instance of this class is created, a `Spectator` is assigned
under the attribute name ``instance_spectator``. When a ``MethodSpectator`` is accessed through an instance,
the descriptor will return a new wrapper function that will redirect to ``Spectator.wrapper``, which triggers
the beforebacks and afterbacks registered to the instance.
