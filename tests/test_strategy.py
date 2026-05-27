"""Tests for captain.strategy"""

import pytest
from captain.strategy import ResourceBudget, Strategy, StrategyEngine


class TestResourceBudget:
    def test_can_allocate(self):
        b = ResourceBudget(cpu=2.0, memory=4.0, budget=100.0)
        req = ResourceBudget(cpu=1.0, memory=2.0, budget=50.0)
        assert b.can_allocate(req) is True

    def test_cannot_allocate_over(self):
        b = ResourceBudget(cpu=1.0)
        req = ResourceBudget(cpu=2.0)
        assert b.can_allocate(req) is False

    def test_allocate_and_release(self):
        b = ResourceBudget(cpu=4.0, memory=8.0, budget=200.0)
        req = ResourceBudget(cpu=1.0, memory=2.0, budget=50.0)
        b.allocate(req)
        assert b.cpu == pytest.approx(3.0)
        b.release(req)
        assert b.cpu == pytest.approx(4.0)

    def test_custom_resources(self):
        b = ResourceBudget(custom={"gpu": 4.0})
        req = ResourceBudget(custom={"gpu": 2.0})
        assert b.can_allocate(req) is True
        b.allocate(req)
        assert b.custom["gpu"] == pytest.approx(2.0)

    def test_allocate_insufficient_raises(self):
        b = ResourceBudget(cpu=0.5)
        with pytest.raises(ValueError):
            b.allocate(ResourceBudget(cpu=1.0))


class TestStrategyEngine:
    def _make_engine(self) -> StrategyEngine:
        return StrategyEngine(ResourceBudget(cpu=4.0, memory=8.0, budget=200.0))

    def test_add_and_plan(self):
        engine = self._make_engine()
        engine.add_strategy(Strategy(id="s1", name="Alpha", priority=5, resources=ResourceBudget(cpu=1.0)))
        engine.add_strategy(Strategy(id="s2", name="Beta", priority=10, resources=ResourceBudget(cpu=1.0)))
        plan = engine.plan()
        assert plan[0].name == "Beta"

    def test_activate(self):
        engine = self._make_engine()
        engine.add_strategy(Strategy(id="s1", resources=ResourceBudget(cpu=2.0, memory=4.0, budget=50.0)))
        alloc = engine.activate("s1")
        assert alloc.strategy_id == "s1"
        assert engine.available.cpu == pytest.approx(2.0)
        assert len(engine.active_strategies) == 1

    def test_deactivate_releases(self):
        engine = self._make_engine()
        engine.add_strategy(Strategy(id="s1", resources=ResourceBudget(cpu=2.0)))
        engine.activate("s1")
        engine.deactivate("s1")
        assert engine.available.cpu == pytest.approx(4.0)
        assert len(engine.active_strategies) == 0

    def test_plan_skips_infeasible(self):
        engine = StrategyEngine(ResourceBudget(cpu=1.0))
        engine.add_strategy(Strategy(id="s1", priority=10, resources=ResourceBudget(cpu=2.0)))
        engine.add_strategy(Strategy(id="s2", priority=5, resources=ResourceBudget(cpu=0.5)))
        plan = engine.plan()
        ids = [s.id for s in plan]
        assert "s1" not in ids
        assert "s2" in ids
