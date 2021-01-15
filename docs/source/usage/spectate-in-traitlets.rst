Spectate in Traitlets
=====================

The inspiration for Spectate originally came from difficulties encountered while working
with mutable data types in `IPython's Traitlets <https://github.com/ipython/traitlets/>`__.
Unfortunately Traitlets does not natively allows you to track changes to mutable data
types.

Now though, with Spectate, we can add this functionality to traitlets using a custom
``TraitType`` that can act as a base class for all mutable traits.

.. code-block::

    from spectate import mvc
    from traitlets import TraitType


    class Mutable(TraitType):
        """A base class for mutable traits using Spectate"""

        # Overwrite this in a subclass.
        _model_type = None

        # The event type observers must track to spectate changes to the model
        _event_type = "mutation"

        # You can dissallow attribute assignment to avoid discontinuities in the
        # knowledge observers have about the state of the model. Removing the line below
        # will enable attribute assignment and require observers to track 'change'
        # events as well as 'mutation' events in to avoid such discontinuities.
        __set__ = None

        def default(self, obj):
            """Create the initial model instance

            The value returned here will be mutated by users of the HasTraits object
            it is assigned to. The resulting events will be tracked in the ``callback``
            defined below and distributed to event observers.
            """
            model = self._model_type()

            @mvc.view(model)
            def callback(model, events):
                obj.notify_change(
                    dict(
                        self._make_change(model, events),
                        name=self.name,
                        type=self._event_type,
                    )
                )

            return model

        def _make_change(self, model, events):
            """Construct a dictionary describing the change"""
            raise NotImplementedError()

With this in place we can then subclass our base ``Mutable`` class and use it to create
a ``MutableDict``:

.. code-block::


    class MutableDict(Mutable):
        """A mutable dictionary trait"""

        _model_type = mvc.Dict

        def _make_change(self, model, events):
            old, new = {}, {}
            for e in events:
                old[e["key"]] = e["old"]
                new[e["key"]] = e["new"]
            return {"value": model, "old": old, "new": new}

An example usage of this trait would then look like:

.. code-block::

    from traitlets import HasTraits, observe


    class MyObject(HasTraits):
        mutable_dict = MutableDict()

        @observe("mutable_dict", type="mutation")
        def track_mutations_from_method(self, change):
            print("method observer:", change)


    def track_mutations_from_function(change):
        print("function observer:", change)


    my_object = MyObject()
    my_object.observe(track_mutations_from_function, "mutable_dict", type="mutation")


    my_object.mutable_dict["x"] = 1
    my_object.mutable_dict.update(x=2, y=3)

.. code-block:: text

    method observer: {'old': {'x': Undefined}, 'new': {'x': 1}, 'name': 'mutable_dict', 'type': 'mutation'}
    function observer: {'old': {'x': Undefined}, 'new': {'x': 1}, 'name': 'mutable_dict', 'type': 'mutation'}
    method observer: {'old': {'x': 1, 'y': Undefined}, 'new': {'x': 2, 'y': 3}, 'name': 'mutable_dict', 'type': 'mutation'}
    function observer: {'old': {'x': 1, 'y': Undefined}, 'new': {'x': 2, 'y': 3}, 'name': 'mutable_dict', 'type': 'mutation'}
