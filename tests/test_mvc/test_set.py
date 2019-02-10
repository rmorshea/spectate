import pytest

from spectate import mvc

from .mock import model_events, events_to_comparable_list


_method_call_and_expected_event = [
    {
        "value": {1, 2, 3},
        "method": "clear",
        "args": [],
        "kwargs": {},
        "events": [{"old": {1, 2, 3}, "new": set()}],
    },
    {
        "value": set(),
        "method": "update",
        "args": [[1, 2, 3]],
        "kwargs": {},
        "events": [{"old": set(), "new": {1, 2, 3}}],
    },
    {
        "value": set(),
        "method": "add",
        "args": [1],
        "kwargs": {},
        "events": [{"old": set(), "new": {1}}],
    },
    {
        "value": {1},
        "method": "remove",
        "args": [1],
        "kwargs": {},
        "events": [{"old": {1}, "new": set()}],
    },
    {
        "value": {1},
        "method": "pop",
        "args": [],
        "kwargs": {},
        "events": [{"old": {1}, "new": set()}],
    },
    {
        "value": {1},
        "method": "discard",
        "args": [1],
        "kwargs": {},
        "events": [{"old": {1}, "new": set()}],
    },
    {"value": {1}, "method": "discard", "args": [2], "kwargs": {}, "events": []},
    {
        "value": {1, 2, 3},
        "method": "intersection_update",
        "args": [{2, 3, 4}],
        "kwargs": {},
        "events": [{"old": {1}, "new": set()}],
    },
    {
        "value": {1, 2, 3},
        "method": "symmetric_difference_update",
        "args": [{2, 3, 4}],
        "kwargs": {},
        "events": [{"old": {2, 3}, "new": {4}}],
    },
]


@pytest.mark.parametrize("expectation", _method_call_and_expected_event)
def test_basic_events(expectation):
    value, actual_events = model_events(mvc.Set, expectation["value"])
    method = getattr(value, expectation["method"])
    args = expectation.get("args", [])
    kwargs = expectation.get("kwargs", {})
    method(*args, **kwargs)
    expected_events = expectation["events"]
    assert events_to_comparable_list(actual_events) == events_to_comparable_list(
        expected_events
    )
