Spectate |release|
==================

A library that can track changes to mutable data types. With :mod:`spectate` complicated
protocols for managing updates, don't need to be the outward responsibility of a user,
and can instead be done automagically in the background.

.. toctree::
    :maxdepth: 2

    install
    usage/index
    api/index

At A Glance
-----------

If you're using Python 3.6 and above, create a :mod:`spectate.mvc` object

.. code-block:: python

    from spectate import mvc

    l = mvc.List()

Register a view function to it that observes changes

.. code-block:: python

    @mvc.view(l)
    def printer(l, events):
        for e in events:
            print(e)

Then modify your object and watch the view function react

.. code-block:: python

    l.append(0)
    l[0] = 1
    l.extend([2, 3])

.. code-block:: text

    {'index': 0, 'old': Undefined, 'new': 0}
    {'index': 0, 'old': 0, 'new': 1}
    {'index': 1, 'old': Undefined, 'new': 2}
    {'index': 2, 'old': Undefined, 'new': 3}
