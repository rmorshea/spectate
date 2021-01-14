from contextlib import contextmanager
from typing import Iterator, Callable, Optional, List

from .base import Model, Event, TupleOfEvents

__all__ = ["hold", "mute", "rollback"]


_EventReducerFunc = Callable[[Model, List[Event]], List[Event]]


@contextmanager
def hold(
    model: Model, reducer: Optional[_EventReducerFunc] = None
) -> Iterator[List[Event]]:
    """Temporarilly withold change events in a modifiable list.

    All changes that are captured within a "hold" context are forwarded to a list
    which is yielded to the user before being sent to views of the given ``model``.
    If desired, the user may modify the list of events before the context is left in
    order to change the events that are ultimately sent to the model's views.

    Parameters:
        model:
            The model object whose change events will be temporarilly witheld.
        reducer:
            A function for modifying the events list at the end of the context.
            Its signature is ``(model, events) -> new_events`` where ``model`` is the
            given model, ``events`` is the complete list of events produced in the
            context, and the returned ``new_events`` is a list of events that will
            actuall be distributed to views.

    Notes:
        All changes witheld from views will be sent as a single notification. For
        example if you view a :class:`specate.mvc.models.List` and its ``append()``
        method is called three times within a :func:`hold` context,


    Examples:
        Note how the event from ``l.append(1)`` is omitted from the printed statements.

        .. code-block:: python

            from spectate import mvc

            l = mvc.List()

            mvc.view(d, lambda d, e: list(map(print, e)))

            with mvc.hold(l) as events:
                l.append(1)
                l.append(2)

                del events[0]

        .. code-block:: text

            {'index': 1, 'old': Undefined, 'new': 2}
    """
    if not isinstance(model, Model):
        raise TypeError("Expected a Model, not %r." % model)
    events: List[Event] = []
    restore = model.__dict__.get("_notify_model_views")
    model._notify_model_views = lambda e: events.extend(e)  # type: ignore

    try:
        yield events
    finally:
        if restore is None:
            del model._notify_model_views
        else:
            model._notify_model_views = restore  # type: ignore

        if reducer is not None:
            events = reducer(model, events)

        model._notify_model_views(tuple(events))


@contextmanager
def rollback(
    model: Model,
    undo: Callable[[Model, TupleOfEvents, Exception], None] = None,
    reducer: Optional[_EventReducerFunc] = None,
) -> Iterator[None]:
    """Withold events if an error occurs.

    Generall operate

    Parameters:
        model:
            The model object whose change events may be witheld.
        undo:
            An optional function for reversing any changes that may have taken place.
            Its signature is ``(model, events, error)`` where ``model`` is the given
            model, ``events`` is a list of all the events that took place, and ``error``
            is the exception that was riased. Any changes that you make to the model
            within this function will not produce events.

    Examples:

        Simple supression of events:

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

        Undo changes for a dictionary:

        .. code-block:: python

            from spectate import mvc

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

        .. code-block:: python

            {'a': 1, 'b': 2}
            {}
    """
    with hold(model, reducer=reducer) as events:
        try:
            yield None
        except Exception as error:
            if undo is not None:
                with mute(model):
                    undo(model, tuple(events), error)
            events.clear()
            raise


@contextmanager
def mute(model: Model) -> Iterator[None]:
    """Block a model's views from being notified.

    All changes within a "mute" context will be blocked. No content is yielded to the
    user as in :func:`hold`, and the views of the model are never notified that changes
    took place.

    Parameters:
        mode: The model whose change events will be blocked.

    Examples:

        The view is never called due to the :func:`mute` context:

        .. code-block:: python

            from spectate import mvc

            l = mvc.List()

            @mvc.view(l)
            def raises(events):
                raise ValueError("Events occured!")

            with mvc.mute(l):
                l.append(1)
    """
    if not isinstance(model, Model):
        raise TypeError("Expected a Model, not %r." % model)
    restore = model.__dict__.get("_notify_model_views")
    model._notify_model_views = lambda e: None  # type: ignore
    try:
        yield None
    finally:
        if restore is None:
            del model._notify_model_views
        else:
            model._notify_model_views = restore  # type: ignore
