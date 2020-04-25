import pytest

from spectate import mvc
from spectate.mvc import Undefined as undef

from .mock import model_events, events_to_comparable_list


_method_call_and_expected_event = [
    {
        "value": {"a": None},
        "method": "__setitem__",
        "args": ["a", 1],
        "kwargs": {},
        "events": [{"old": None, "new": 1, "key": "a"}],
    },
    {
        "value": {},
        "method": "__setitem__",
        "args": ["a", 1],
        "kwargs": {},
        "events": [{"old": undef, "new": 1, "key": "a"}],
    },
    {
        "value": {"a": None},
        "method": "setdefault",
        "args": ["a", 1],
        "kwargs": {},
        "events": [],
    },
    {
        "value": {},
        "method": "setdefault",
        "args": ["a", 1],
        "kwargs": {},
        "events": [{"old": undef, "new": 1, "key": "a"}],
    },
    {
        "value": {"a": 1},
        "method": "__delitem__",
        "args": ["a"],
        "kwargs": {},
        "events": [{"old": 1, "new": undef, "key": "a"}],
    },
    {
        "value": {"a": 1},
        "method": "pop",
        "args": ["a"],
        "kwargs": {},
        "events": [{"old": 1, "new": undef, "key": "a"}],
    },
    {
        "value": {},
        "method": "update",
        "args": [{"a": 1, "b": 2}],
        "kwargs": {},
        "events": [
            {"old": undef, "new": 1, "key": "a"},
            {"old": undef, "new": 2, "key": "b"},
        ],
    },
    {
        "value": {"a": None, "b": None},
        "method": "update",
        "args": [{"a": 1, "b": 2}],
        "kwargs": {},
        "events": [
            {"old": None, "new": 1, "key": "a"},
            {"old": None, "new": 2, "key": "b"},
        ],
    },
    {
        "value": {"a": 1, "b": 2},
        "method": "clear",
        "args": [],
        "kwargs": {},
        "events": [
            {"old": 1, "new": undef, "key": "a"},
            {"old": 2, "new": undef, "key": "b"},
        ],
    },
    {"value": {}, "method": "clear", "args": [], "kwargs": {}, "events": []},
]


@pytest.mark.parametrize("expectation", _method_call_and_expected_event)
def test_basic_events(expectation):
    value, actual_events = model_events(mvc.Dict, expectation["value"])
    method = getattr(value, expectation["method"])
    args = expectation.get("args", [])
    kwargs = expectation.get("kwargs", {})
    method(*args, **kwargs)
    expected_events = expectation["events"]
    assert events_to_comparable_list(actual_events) == events_to_comparable_list(
        expected_events
    )
