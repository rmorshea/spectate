import pytest

from spectate import mvc
from spectate.mvc import Undefined as undef

from .mock import model_events, events_to_comparable_list


_method_call_and_expected_event = [
    {
        "value": {},
        "method": "__setattr__",
        "args": ["a", 1],
        "kwargs": {},
        "events": [{"old": undef, "new": 1, "attr": "a"}],
    },
    {
        "value": {"a": None},
        "method": "__setattr__",
        "args": ["a", 1],
        "kwargs": {},
        "events": [{"old": None, "new": 1, "attr": "a"}],
    },
    {
        "value": {"a": 1},
        "method": "__delattr__",
        "args": ["a"],
        "kwargs": {},
        "events": [{"old": 1, "new": undef, "attr": "a"}],
    },
]


@pytest.mark.parametrize("expectation", _method_call_and_expected_event)
def test_basic_events(expectation):
    value, actual_events = model_events(mvc.Object, expectation["value"])
    method = getattr(value, expectation["method"])
    args = expectation.get("args", [])
    kwargs = expectation.get("kwargs", {})
    method(*args, **kwargs)
    expected_events = expectation["events"]
    assert events_to_comparable_list(actual_events) == events_to_comparable_list(
        expected_events
    )
