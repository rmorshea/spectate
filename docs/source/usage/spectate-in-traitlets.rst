Spectate in Traitlets
=====================

The inspiration for Spectate originally came from difficulties encountered while working
with `IPython's Traitlets <https://github.com/ipython/traitlets/>`__ because the builtin
capabilities of ``traitlets`` don't allow you to track changes to mutable data types.

Now though, with Spectate, we can add this functionality to traitlets with a custom
``TraitType`` which can act as a base class for all mutable traits.

.. code-block::

    from spectate import mvc
    from traitlets import TraitType, HasTraits, observe


    class Mutable(TraitType):
        """A base class for mutable traits using Spectate"""

        _model_type = None
        _event_type = None

        def instance_init(self, obj):
            default = self._model_type()

            @mvc.view(default)
            def callback(default, events):
                change = dict(
                    self._make_change(events),
                    name=self.name,
                    type=self._event_type,
                )
                obj.notify_change(change)

            setattr(obj, self.name, default)

        def _make_change(self, events):
            raise NotImplementedError()

With this in place we can then subclass our base ``Mutable`` class and use it to create
a ``MutableDict``:

.. code-block::

    class MutableDict(Mutable):
        """A mutable dictionary trait"""

        _model_type = mvc.Dict
        _event_type = "item"

        def _make_change(self, events):
            change = {"old": {}, "new": {}}
            for e in events:
                change["new"][e.key] = e.new
                change["old"][e.key] = e.old
            return change
