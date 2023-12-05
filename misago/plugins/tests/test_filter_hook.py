import pytest

from ..hooks import FilterHook

ACTION = 0
FIRST_FILTER = 1
SECOND_FILTER = 2


class MockFilterHook(FilterHook):
    def __call__(self, action):
        return super().__call__(action, [])


def action(data):
    data.append(ACTION)
    return data


def first_filter(action, data):
    data = action(data)
    data.append(FIRST_FILTER)
    return data


def second_filter(action, data):
    data = action(data)
    data.append(SECOND_FILTER)
    return data


@pytest.fixture
def hook():
    return MockFilterHook()


def test_filter_hook_without_filters_just_calls_action(hook):
    assert hook(action) == [ACTION]


def test_filter_hook_calls_filter_before_action(hook):
    hook.append(first_filter)
    assert hook(action) == [ACTION, FIRST_FILTER]


def test_filter_hook_calls_filters_in_order_of_adding(hook):
    hook.append(first_filter)
    hook.append(second_filter)
    assert hook(action) == [ACTION, FIRST_FILTER, SECOND_FILTER]


def test_filter_can_be_inserted_before_other_filters(hook):
    hook.append(first_filter)
    hook.prepend(second_filter)
    assert hook(action) == [ACTION, SECOND_FILTER, FIRST_FILTER]
