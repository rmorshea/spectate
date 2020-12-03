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

    _control_change = mvc.Control(
        ["increment", "decrement"],
        before="_control_before_change",
        after="_control_after_change",
    )

    def _control_before_change(self, call, notify):
        return self.value

    def _control_after_change(self, answer, notify):
        notify(old=answer["before"], new=self.value)
