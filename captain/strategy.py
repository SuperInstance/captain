"""StrategyEngine — adaptive planning and resource allocation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ResourceBudget:
    """A budget of resources available for allocation."""

    cpu: float = 1.0
    memory: float = 1.0
    budget: float = 100.0
    custom: dict[str, float] = field(default_factory=dict)

    def can_allocate(self, request: ResourceBudget) -> bool:
        if request.cpu > self.cpu:
            return False
        if request.memory > self.memory:
            return False
        if request.budget > self.budget:
            return False
        for key, val in request.custom.items():
            if self.custom.get(key, 0.0) < val:
                return False
        return True

    def allocate(self, request: ResourceBudget) -> None:
        if not self.can_allocate(request):
            raise ValueError("Insufficient resources")
        self.cpu -= request.cpu
        self.memory -= request.memory
        self.budget -= request.budget
        for key, val in request.custom.items():
            self.custom[key] = self.custom.get(key, 0.0) - val

    def release(self, amount: ResourceBudget) -> None:
        self.cpu += amount.cpu
        self.memory += amount.memory
        self.budget += amount.budget
        for key, val in amount.custom.items():
            self.custom[key] = self.custom.get(key, 0.0) + val


@dataclass
class Strategy:
    """A named strategy with phases and resource requirements."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    phases: list[str] = field(default_factory=list)
    resources: ResourceBudget = field(default_factory=ResourceBudget)
    priority: int = 0  # higher = more important
    active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Allocation:
    """Record of a resource allocation to a strategy."""

    strategy_id: str
    resources: ResourceBudget
    timestamp: datetime = field(default_factory=datetime.now)


class StrategyEngine:
    """Plans and allocates resources across competing strategies."""

    def __init__(self, total_budget: ResourceBudget | None = None) -> None:
        self.total_budget = total_budget or ResourceBudget()
        self.available = ResourceBudget(
            cpu=self.total_budget.cpu,
            memory=self.total_budget.memory,
            budget=self.total_budget.budget,
            custom=dict(self.total_budget.custom),
        )
        self._strategies: dict[str, Strategy] = {}
        self._allocations: list[Allocation] = []

    # --- strategy management ---

    def add_strategy(self, strategy: Strategy) -> None:
        if strategy.id in self._strategies:
            raise ValueError(f"Strategy {strategy.id} already exists")
        self._strategies[strategy.id] = strategy

    def remove_strategy(self, strategy_id: str) -> Strategy:
        if strategy_id not in self._strategies:
            raise KeyError(f"No strategy {strategy_id}")
        return self._strategies.pop(strategy_id)

    def get_strategy(self, strategy_id: str) -> Strategy:
        return self._strategies[strategy_id]

    @property
    def strategies(self) -> list[Strategy]:
        return list(self._strategies.values())

    # --- planning ---

    def plan(self) -> list[Strategy]:
        """Return strategies ordered by priority (high → low), considering feasibility."""
        ranked = sorted(
            self._strategies.values(),
            key=lambda s: s.priority,
            reverse=True,
        )
        feasible: list[Strategy] = []
        for s in ranked:
            if self.available.can_allocate(s.resources):
                feasible.append(s)
        return feasible

    def activate(self, strategy_id: str) -> Allocation:
        """Activate a strategy by allocating its required resources."""
        strategy = self.get_strategy(strategy_id)
        self.available.allocate(strategy.resources)
        strategy.active = True
        alloc = Allocation(strategy_id=strategy.id, resources=strategy.resources)
        self._allocations.append(alloc)
        return alloc

    def deactivate(self, strategy_id: str) -> None:
        strategy = self.get_strategy(strategy_id)
        if not strategy.active:
            return
        self.available.release(strategy.resources)
        strategy.active = False

    @property
    def allocations(self) -> list[Allocation]:
        return list(self._allocations)

    @property
    def active_strategies(self) -> list[Strategy]:
        return [s for s in self._strategies.values() if s.active]
