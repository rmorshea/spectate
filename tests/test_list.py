import pytest

from spectate import mvc
from spectate.mvc import Undefined as undef

from .mock import model_events, events_to_comparable_list


_method_call_and_expected_event = [
    {
        "value": [1, 2, 3],
        "method": "__setitem__",
        "args": [1, 5],
        "kwargs": {},
        "events": [{"old": 2, "new": 5, "index": 1}],
    },
    {
        "value": [1, 2, 3],
        "method": "__delitem__",
        "args": [0],
        "kwargs": {},
        "events": [
            {"old": 1, "new": 2, "index": 0},
            {"old": 2, "new": 3, "index": 1},
            {"old": 3, "new": undef, "index": 2},
        ],
    },
    {
        "value": [1, 2, 3],
        "method": "append",
        "args": [4],
        "kwargs": {},
        "events": [{"old": undef, "new": 4, "index": 3}],
    },
    {
        "value": [1, 2, 3],
        "method": "pop",
        "args": [],
        "kwargs": {},
        "events": [{"old": 3, "new": undef, "index": 2}],
    },
    {
        "value": [1, 2, 3],
        "method": "pop",
        "args": [0],
        "kwargs": {},
        "events": [
            {"old": 1, "new": 2, "index": 0},
            {"old": 2, "new": 3, "index": 1},
            {"old": 3, "new": undef, "index": 2},
        ],
    },
    {
        "value": [2, 3],
        "method": "insert",
        "args": [0, 1],
        "kwargs": {},
        "events": [
            {"old": 2, "new": 1, "index": 0},
            {"old": 3, "new": 2, "index": 1},
            {"old": undef, "new": 3, "index": 2},
        ],
    },
    {
        "value": [],
        "method": "extend",
        "args": [[1, 2, 3]],
        "kwargs": {},
        "events": [
            {"old": undef, "new": 1, "index": 0},
            {"old": undef, "new": 2, "index": 1},
            {"old": undef, "new": 3, "index": 2},
        ],
    },
    {
        "value": [],
        "method": "extend",
        "args": [(i for i in range(1, 4))],
        "kwargs": {},
        "events": [
            {"old": undef, "new": 1, "index": 0},
            {"old": undef, "new": 2, "index": 1},
            {"old": undef, "new": 3, "index": 2},
        ],
    },
    {
        "value": [1, 2, 3],
        "method": "clear",
        "args": [],
        "kwargs": {},
        "events": [
            {"old": 1, "new": undef, "index": 0},
            {"old": 2, "new": undef, "index": 1},
            {"old": 3, "new": undef, "index": 2},
        ],
    },
    {"value": [], "method": "clear", "args": [], "kwargs": {}, "events": []},
    {
        "value": [1, 2, 3],
        "method": "remove",
        "args": [1],
        "kwargs": {},
        "events": [
            {"old": 1, "new": 2, "index": 0},
            {"old": 2, "new": 3, "index": 1},
            {"old": 3, "new": undef, "index": 2},
        ],
    },
    {
        "value": [3, 2, 1],
        "method": "sort",
        "args": [],
        "kwargs": {},
        "events": [{"old": 3, "new": 1, "index": 0}, {"old": 1, "new": 3, "index": 2}],
    },
    {
        "value": [1, 2, 3],
        "method": "reverse",
        "args": [],
        "kwargs": {},
        "events": [{"old": 1, "new": 3, "index": 0}, {"old": 3, "new": 1, "index": 2}],
    },
]


@pytest.mark.parametrize("expectation", _method_call_and_expected_event)
def test_basic_events(expectation):
    value, actual_events = model_events(mvc.List, expectation["value"])
    method = getattr(value, expectation["method"])
    args = expectation.get("args", [])
    kwargs = expectation.get("kwargs", {})
    method(*args, **kwargs)
    expected_events = expectation["events"]
    assert events_to_comparable_list(actual_events) == events_to_comparable_list(
        expected_events
    )
