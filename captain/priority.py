"""PriorityQueue — weighted scoring, deadlines, and dependency ordering."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


class Priority(enum.Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class Task:
    """A task with priority, optional deadline, and dependencies."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    priority: Priority = Priority.MEDIUM
    weight: float = 1.0  # extra scoring multiplier
    deadline: datetime | None = None
    dependencies: list[str] = field(default_factory=list)  # task IDs
    completed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def effective_score(self) -> float:
        """Compute a composite urgency score (higher = more urgent)."""
        base = self.priority.value * self.weight
        if self.deadline:
            remaining = (self.deadline - datetime.now()).total_seconds()
            # Urgency ramp: score increases as deadline approaches
            if remaining < 0:
                base += 50  # overdue gets big boost
            elif remaining < 3600:
                base += 20  # <1h
            elif remaining < 86400:
                base += 10  # <1d
        return base


class PriorityQueue:
    """Priority queue with weighted scoring, deadlines, and dependency ordering."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        if task.id in self._tasks:
            raise ValueError(f"Task {task.id} already exists")
        self._tasks[task.id] = task

    def remove(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"No task {task_id}")
        return self._tasks.pop(task_id)

    def complete(self, task_id: str) -> Task:
        task = self.remove(task_id)
        task.completed = True
        return task

    def get(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"No task {task_id}")
        return self._tasks[task_id]

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    @property
    def size(self) -> int:
        return len(self._tasks)

    def peek(self) -> Task | None:
        """Return the highest-priority task whose dependencies are met."""
        ready = self._ready_tasks()
        if not ready:
            return None
        ready.sort(key=lambda t: t.effective_score(), reverse=True)
        return ready[0]

    def pop(self) -> Task | None:
        task = self.peek()
        if task:
            del self._tasks[task.id]
        return task

    def _ready_tasks(self) -> list[Task]:
        """Tasks whose dependencies are all completed (not in queue)."""
        active_ids = set(self._tasks.keys())
        return [
            t for t in self._tasks.values()
            if not any(d in active_ids for d in t.dependencies)
        ]

    def ordered(self) -> list[Task]:
        """Return all tasks in priority order, respecting dependencies."""
        result: list[Task] = []
        remaining = dict(self._tasks)
        while remaining:
            active_ids = set(remaining.keys())
            ready = [
                t for t in remaining.values()
                if not any(d in active_ids for d in t.dependencies)
            ]
            if not ready:
                # Circular dependency — break by picking highest score
                ready = list(remaining.values())
            ready.sort(key=lambda t: t.effective_score(), reverse=True)
            picked = ready[0]
            result.append(picked)
            del remaining[picked.id]
        return result

    def overdue(self) -> list[Task]:
        now = datetime.now()
        return [
            t for t in self._tasks.values()
            if t.deadline and t.deadline < now
        ]

    def due_within(self, delta: timedelta) -> list[Task]:
        cutoff = datetime.now() + delta
        return [
            t for t in self._tasks.values()
            if t.deadline and t.deadline <= cutoff
        ]
