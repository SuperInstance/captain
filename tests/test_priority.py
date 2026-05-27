"""Tests for captain.priority"""

from datetime import datetime, timedelta

import pytest
from captain.priority import Priority, PriorityQueue, Task


class TestTask:
    def test_effective_score_base(self):
        t = Task(priority=Priority.HIGH, weight=2.0)
        assert t.effective_score() == pytest.approx(6.0)

    def test_effective_score_overdue(self):
        t = Task(priority=Priority.LOW, deadline=datetime.now() - timedelta(hours=1))
        assert t.effective_score() > Priority.LOW.value


class TestPriorityQueue:
    def _make_task(self, tid: str, priority: Priority = Priority.MEDIUM, **kw) -> Task:
        return Task(id=tid, title=f"Task-{tid}", priority=priority, **kw)

    def test_add_and_size(self):
        pq = PriorityQueue()
        pq.add(self._make_task("a"))
        pq.add(self._make_task("b"))
        assert pq.size == 2

    def test_add_duplicate_raises(self):
        pq = PriorityQueue()
        pq.add(self._make_task("a"))
        with pytest.raises(ValueError):
            pq.add(self._make_task("a"))

    def test_peek_returns_highest(self):
        pq = PriorityQueue()
        pq.add(self._make_task("low", Priority.LOW))
        pq.add(self._make_task("high", Priority.HIGH))
        assert pq.peek().id == "high"

    def test_pop_removes(self):
        pq = PriorityQueue()
        pq.add(self._make_task("a", Priority.HIGH))
        pq.add(self._make_task("b", Priority.LOW))
        t = pq.pop()
        assert t.id == "a"
        assert pq.size == 1

    def test_pop_empty(self):
        pq = PriorityQueue()
        assert pq.pop() is None

    def test_dependency_ordering(self):
        pq = PriorityQueue()
        pq.add(self._make_task("child", Priority.HIGH, dependencies=["parent"]))
        pq.add(self._make_task("parent", Priority.LOW))
        # parent should come first despite lower priority
        ordered = pq.ordered()
        assert ordered[0].id == "parent"

    def test_peek_waits_for_deps(self):
        pq = PriorityQueue()
        pq.add(self._make_task("child", Priority.HIGH, dependencies=["parent"]))
        pq.add(self._make_task("parent", Priority.LOW))
        assert pq.peek().id == "parent"

    def test_complete(self):
        pq = PriorityQueue()
        pq.add(self._make_task("a"))
        t = pq.complete("a")
        assert t.completed is True
        assert pq.size == 0

    def test_overdue(self):
        pq = PriorityQueue()
        pq.add(Task(id="old", deadline=datetime.now() - timedelta(hours=1)))
        assert len(pq.overdue()) == 1

    def test_due_within(self):
        pq = PriorityQueue()
        pq.add(Task(id="soon", deadline=datetime.now() + timedelta(minutes=30)))
        pq.add(Task(id="later", deadline=datetime.now() + timedelta(days=7)))
        assert len(pq.due_within(timedelta(hours=1))) == 1

    def test_ordered_respects_all_deps(self):
        pq = PriorityQueue()
        pq.add(self._make_task("c", dependencies=["b"]))
        pq.add(self._make_task("b", dependencies=["a"]))
        pq.add(self._make_task("a"))
        ids = [t.id for t in pq.ordered()]
        assert ids.index("a") < ids.index("b") < ids.index("c")
