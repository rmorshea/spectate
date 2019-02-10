from spectate import mvc


def events_to_comparable_list(events):
    return tuple(sorted(tuple(sorted((k, evt[k]) for k in evt)) for evt in events))


def model_events(model, *args, **kwargs):
    cached_events = []

    if not isinstance(model, mvc.Model):
        model = model(*args, **kwargs)

    @mvc.view(model)
    def cache(model, events):
        cached_events.extend(events)

    return model, cached_events


class Counter(mvc.Model):
    def __init__(self):
        self.value = 0

    def increment(self, amount):
        self.value += amount

    def decrement(self, amount):
        self.value -= amount

    # define a beforeback for increment and decrement
    _control_change = mvc.Control("increment", "decrement")

    @_control_change.before
    def _control_change(self, call, notify):
        return self.value

    # create the corresponding afterback
    @_control_change.after
    def _control_change(self, answer, notify):
        # Send an "event" dictionary to the Counter's views.
        notify(old=answer.before, new=self.value)
