The Basics
==========

Spectate defines three main constructs:

1. :class:`models <spectate.base.Model>` - objects which get modified by the user.

2. :func:`views <spectate.base.view>` - functions which receives change events.

3. :class:`controls <spectate.base.Control>` - private attributes of a model which produces change events.

Since the :mod:`mvc <spectate>` module already provides some basic models for us you
don't need to worry about :class:`controls <spectate.base.Control>` yet. Let's begin
by considering a builtin :class:`~spectate.models.Dict` model. We can instantiate
this object just as we would with a standard :class:`dict`:

.. code-block:: python

    from spectate import mvc

    d = mvc.Dict(a=0)

Now though, we can now register a :func:`~spectate.base.view` function with a
decorator. This view function is called any time a change is made to the model ``d``
that causes its data to be mutated.

.. code-block:: python

    @mvc.view(d)  # <----- pass `d` in the decorator to observe its changes
    def printer(
        model,  # <------- The model which experienced an event
        events,  #  <----- A tuple of event dictionaries
    ):
        print("model:", model)
        for e in events:
            print("event:", e)

Change events are passed into this function as a tuple of immutable dict-like objects
containing change information. Each model has its own change event information.
In the case of a :class:`~spectate.models.Dict` the event objects have the fields
``key``, ``old``, and ``new``. So when we change a key in ``d`` we'll find that our
``printer`` view function is called and that it prints out an event object with the
expected information:

.. code-block:: python

    d["a"] = 1

.. code-block:: text

    model: {'a': 1}
    event: {'key': 'a', 'old': 0, 'new': 1}

In cases where a mutation would result in changes to multiple change, one or more event
objects can be broadcast to the view function:

.. code-block:: python

    d.update(b=2, c=3)

.. code-block:: text

    model: {'a': 1, 'b': 2, 'c': 3}
    event: {'key': 'b', 'old': Undefined, 'new': 2}
    event: {'key': 'c', 'old': Undefined, 'new': 3}


Nesting Models
--------------

What if we want to observe changes to nested data structures though? Thankfuly
all of Spectate's :ref:`Builtin Model Types` that inherit from
:class:`~spectate.models.Structure` can handle this automatically whenevener
another model is placed inside another:

.. code-block:: python

    from spectate import mvc

    outer_dict = mvc.Dict()
    inner_dict = mvc.Dict()

    mvc.view(outer_dict, printer)

    outer_dict["x"] = inner_dict
    inner_dict["y"] = 1

.. code-block:: text

    model: {'x': {}}
    event: {'key': 'x', 'old': Undefined, 'new': {}}
    model: {'y': 1}
    event: {'key': 'y', 'old': Undefined, 'new': 1}

This works just as well if you mix data types too:

.. code-block:: python

    from spectate import mvc

    outer_dict = mvc.Dict()
    middle_list = mvc.List()
    inner_obj = mvc.Object()

    mvc.view(outer_dict, printer)

    outer_dict["x"] = middle_list
    middle_list.append(inner_obj)
    inner_obj.y = 1

.. code-block:: text

    model: {'x': []}
    event: {'key': 'x', 'old': Undefined, 'new': []}
    model: [<spectate.models.Object object at 0x7f8041ae9550>]
    event: {'index': 0, 'old': Undefined, 'new': <spectate.models.Object object at 0x7f8041ae9550>}
    model: <spectate.models.Object object at 0x7f8041ae9550>
    event: {'attr': 'y', 'old': Undefined, 'new': 1}

However, note that events on nested data structures don't carry information about the
location of the notifying model. For this you'll need to implement a :ref:`Custom Model`
and add this information to the events manually.


Custom Models
-------------

To create a custom model all you have to do is inherit from :class:`~spectate.base.Model`
and broadcast events with a :func:`~spectate.base.notifier`. To get the idea across,
lets implement a simple counter object that notifies when a value is incremented or
decremented.

.. code-block:

    from spectate import mvc

    class Counter(mvc.Model):

        def __init__(self):
            self.value = 0

        def increment(self):
            self.value += 1
            with mvc.notifier(self) as notify:
                notify(new=self.value)

        def decrement(self):
            self.value -= 1
            with mvc.notifier(self) as notify:
                notify(new=self.value)

    counter = Counter()

    @mvc.view(counter)
    def printer(model, events):
        for e in events:
            print(e)

    counter.increment()
    counter.increment()
    counter.decrement()

.. code-block::

    {'new': 1}
    {'new': 2}
    {'new': 1}

To share or unshare the view functions between two models using the
:func:`~spectate.base.link` and :func:`~spectate.base.unlink` functions respectively.
This is especially useful when creating nested data structures. For example we can
use it to create an observable binary tree:

.. code-block::

    class Node(mvc.Model):

        def __init__(self, data, parent=None):
            if parent is not None:
                mvc.link(parent, self)
            self.parent = parent
            self.left = None
            self.right = None
            self.data = data

        def add(self, data):
            if data <= self.data:
                if self.left is None:
                    self.left = Node(data, self)
                    with mvc.notifier(self) as notify:
                        notify(left=self.left, path=self.path())
                else:
                    self.left.add(data)
            else:
                if self.right is None:
                    self.right = Node(data, self)
                    with mvc.notifier(self) as notify:
                        notify(right=self.right, path=self.path())
                else:
                    self.right.add(data)

        def path(self):
            n = self
            path = []
            while n is not None:
                path.insert(0, n)
                n = n.parent
            return path

        def __repr__(self):
            return f"Node({self.data})"

    root = Node(0)

    mvc.view(root, printer)

    root.add(1)
    root.add(0)
    root.add(5)
    root.add(2)
    root.add(4)
    root.add(3)


.. code-block:: text

    model: Node(0)
    event: {'right': Node(1), 'path': [Node(0)]}
    model: Node(0)
    event: {'left': Node(0), 'path': [Node(0)]}
    model: Node(1)
    event: {'right': Node(5), 'path': [Node(0), Node(1)]}
    model: Node(5)
    event: {'left': Node(2), 'path': [Node(0), Node(1), Node(5)]}
    model: Node(2)
    event: {'right': Node(4), 'path': [Node(0), Node(1), Node(5), Node(2)]}
    model: Node(4)
    event: {'left': Node(3), 'path': [Node(0), Node(1), Node(5), Node(2), Node(4)]}
