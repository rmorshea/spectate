from pytest import raises

from spectate import mvc

from .mock import model_events, Counter


def test_control_is_only_for_model():
    """Controls must be defined on a Model"""
    with raises(RuntimeError):

        class X:
            _control = mvc.Control("something")


def test_control_using_functions():

    calls = []

    def _control_before(value, call, notify):
        calls.append("before")

    def _control_after(value, call, notify):
        calls.append("after")

    class X(mvc.Model):
        def method(self):
            calls.append("during")

        control = mvc.Control("method", before=_control_before, after=_control_after)

    X().method()
    assert calls == ["before", "during", "after"]


def test_control_using_string_reference():

    calls = []

    class X(mvc.Model):
        def method(self):
            pass

        control = mvc.Control("method", before="before", after="after")

        def before(self, call, notify):
            calls.append("before")

        def after(self, answer, notify):
            calls.append("after")

    X().method()
    assert calls == ["before", "after"]


def test_control_events_were_sent():
    counter, events = model_events(Counter)

    counter.increment(1)
    counter.decrement(2)
    counter.increment(3)
    counter.decrement(4)

    assert events == [
        {"old": 0, "new": 1},
        {"old": 1, "new": -1},
        {"old": -1, "new": 2},
        {"old": 2, "new": -2},
    ]


def test_override_control_methods_in_subclass():
    class MyCounter(Counter):
        def _control_before_change(self, call, notify):
            notify(message="before")
            return super()._control_before_change(call, notify)

    counter, events = model_events(MyCounter)

    counter.increment(1)

    assert events == [{"message": "before"}, {"old": 0, "new": 1}]


def test_add_new_control_in_subclass():
    class MyCounter(Counter):

        _added_control = mvc.Control("increment", before="_added_before")

        def _added_before(self, call, notify):
            notify(message="before")

    counter, events = model_events(MyCounter)

    counter.increment(1)

    assert events == [{"message": "before"}, {"old": 0, "new": 1}]


def test_structure_events():
    class Container(mvc.Structure):
        def __init__(self, name):
            self.name = name
            self.value = None

        def set(self, value):
            self.value = value

        _control_changes = mvc.Control(
            "set", before="_before_change", after="_after_change"
        )

        def _before_change(self, call, notify):
            return self.value

        def _after_change(self, answer, notify):
            notify(old=answer["before"], new=self.value)

        def __repr__(self):
            return "Container(%r)" % self.name

    s0 = Container("s0")
    s1 = Container("s1")
    s2 = Container("s2")

    calls = []

    @mvc.view(s0)
    def on_change(value, events):
        calls.append(value)

    s0.set(s1)
    s1.set(s2)
    s2.set(None)

    assert calls == [s0, s1, s2]
    calls.clear()

    # remove children
    s0.set(None)

    assert calls == [s0]
    calls.clear()

    # these should not trigger events because they are no longer
    # attached to the root container s0
    s1.set(None)
    s2.set(None)

    assert not calls


def test_notifier_context_manager():
    calls = []
    m = mvc.Model()

    @mvc.view(m)
    def viewer(m, events):
        calls.extend(events)

    with mvc.notifier(m) as notify:
        notify(data=1)
        assert calls == []

    assert calls == [{"data": 1}]
    calls.clear()

    with mvc.notifier(m) as notify:
        notify(data=1)
        notify(data=2)

    assert calls == [{"data": 1}, {"data": 2}]


def test_link_and_unlink_inner_models():
    calls = []

    parent = mvc.Model()
    child = mvc.Model()
    grandchild = mvc.Model()

    mvc.link(parent, child)
    mvc.link(child, grandchild)

    def trigger_events():
        with mvc.notifier(grandchild) as notify:
            notify({"data": 1})
        with mvc.notifier(child) as notify:
            notify({"data": 2})
        with mvc.notifier(parent) as notify:
            notify({"data": 3})
        copy = calls[:]
        calls.clear()
        return copy

    @mvc.view(parent)
    def viewer(value, events):
        calls.append({"v": value, "e": list(events)})

    assert trigger_events() == [
        {"v": grandchild, "e": [{"data": 1}]},
        {"v": child, "e": [{"data": 2}]},
        {"v": parent, "e": [{"data": 3}]},
    ]

    mvc.unlink(child, grandchild)
    assert trigger_events() == [
        {"v": child, "e": [{"data": 2}]},
        {"v": parent, "e": [{"data": 3}]},
    ]

    mvc.unlink(parent, child)
    assert trigger_events() == [{"v": parent, "e": [{"data": 3}]}]


def test_unlink_middleman_stops_view_of_leaf_models():
    calls = []

    parent = mvc.Model()
    child = mvc.Model()
    grandchild = mvc.Model()

    mvc.link(parent, child)
    mvc.link(child, grandchild)

    def trigger_events():
        with mvc.notifier(grandchild) as notify:
            notify({"data": 1})
        with mvc.notifier(child) as notify:
            notify({"data": 2})
        with mvc.notifier(parent) as notify:
            notify({"data": 3})
        copy = calls[:]
        calls.clear()
        return copy

    @mvc.view(parent)
    def viewer(value, events):
        calls.append({"v": value, "e": list(events)})

    mvc.unlink(parent, child)

    assert trigger_events() == [{"v": parent, "e": [{"data": 3}]}]
