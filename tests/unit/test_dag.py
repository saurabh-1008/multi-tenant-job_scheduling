import pytest

from app.scheduler.dag import topological_order, get_ready_tasks, CycleError


def test_simple_order():
    tasks = [
        {"name": "a", "depends_on": []},
        {"name": "b", "depends_on": ["a"]},
        {"name": "c", "depends_on": ["a", "b"]},
    ]
    order = topological_order(tasks)
    assert order.index("a") < order.index("b") < order.index("c")


def test_cycle_detection():
    tasks = [
        {"name": "a", "depends_on": ["b"]},
        {"name": "b", "depends_on": ["a"]},
    ]
    with pytest.raises(CycleError):
        topological_order(tasks)


def test_ready_tasks():
    tasks = [
        {"name": "a", "depends_on": []},
        {"name": "b", "depends_on": ["a"]},
    ]
    assert get_ready_tasks(tasks, completed=set()) == ["a"]
    assert get_ready_tasks(tasks, completed={"a"}) == ["b"]