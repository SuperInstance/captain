"""Coverage gap tests — targeting uncovered lines in strategy, priority, report, captain, fleet."""
import pytest
from datetime import datetime, timedelta

from captain.strategy import ResourceBudget, Strategy, StrategyEngine, Allocation
from captain.priority import Priority, Task, PriorityQueue
from captain.report import HealthStatus, Metric, Recommendation, StatusReport
from captain.captain import Captain, LeadershipStyle, TeamMember, Decision
from captain.fleet import FleetCoordination, FleetVessel, VesselStatus


# ── strategy.py coverage gaps ──────────────────────────────────
# Missing lines: 24, 26, 29, 46, 89, 93-95, 102, 131, 137


class TestStrategyDefaultId:
    def test_strategy_default_id(self):
        """Strategy auto-generates an id (line 24)."""
        s = Strategy()
        assert s.id  # non-empty
        assert isinstance(s.id, str)

    def test_strategy_default_phases(self):
        """Strategy has empty phases list by default (line 26)."""
        s = Strategy()
        assert s.phases == []

    def test_strategy_default_metadata(self):
        """Strategy has empty metadata by default (line 29)."""
        s = Strategy()
        assert s.metadata == {}

    def test_strategy_with_phases_and_metadata(self):
        s = Strategy(name="Test", phases=["phase1", "phase2"], metadata={"key": "val"})
        assert s.phases == ["phase1", "phase2"]
        assert s.metadata["key"] == "val"

    def test_strategy_active_default_false(self):
        s = Strategy()
        assert s.active is False


class TestStrategyEngineEdgeCases:
    def test_add_duplicate_strategy_raises(self):
        """Adding a strategy with existing id raises ValueError (line 46)."""
        engine = StrategyEngine()
        engine.add_strategy(Strategy(id="s1"))
        with pytest.raises(ValueError, match="already exists"):
            engine.add_strategy(Strategy(id="s1"))

    def test_activate_feasibility_check(self):
        """Activate should work when resources are available (lines 89, 93-95)."""
        engine = StrategyEngine(ResourceBudget(cpu=4.0, memory=8.0, budget=200.0))
        s = Strategy(id="s1", resources=ResourceBudget(cpu=2.0, memory=4.0, budget=50.0))
        engine.add_strategy(s)
        alloc = engine.activate("s1")
        assert isinstance(alloc, Allocation)
        assert alloc.strategy_id == "s1"
        assert s.active is True
        # available should be reduced
        assert engine.available.cpu == pytest.approx(2.0)
        assert engine.available.memory == pytest.approx(4.0)
        assert engine.available.budget == pytest.approx(150.0)

    def test_activate_with_custom_resources(self):
        """Activate with custom resources (line 102)."""
        engine = StrategyEngine(ResourceBudget(custom={"gpu": 4.0}))
        s = Strategy(id="s1", resources=ResourceBudget(custom={"gpu": 2.0}))
        engine.add_strategy(s)
        engine.activate("s1")
        assert engine.available.custom["gpu"] == pytest.approx(2.0)

    def test_deactivate_already_inactive(self):
        """Deactivating a non-active strategy is a no-op (line 131)."""
        engine = StrategyEngine()
        engine.add_strategy(Strategy(id="s1"))
        engine.deactivate("s1")  # should not raise
        assert len(engine.active_strategies) == 0

    def test_allocations_property(self):
        """Allocations property returns list (line 137)."""
        engine = StrategyEngine(ResourceBudget(cpu=10.0))
        engine.add_strategy(Strategy(id="s1", resources=ResourceBudget(cpu=1.0)))
        engine.activate("s1")
        assert len(engine.allocations) == 1

    def test_remove_strategy(self):
        engine = StrategyEngine()
        s = Strategy(id="s1")
        engine.add_strategy(s)
        removed = engine.remove_strategy("s1")
        assert removed.id == "s1"
        assert len(engine.strategies) == 0

    def test_remove_strategy_not_found(self):
        engine = StrategyEngine()
        with pytest.raises(KeyError):
            engine.remove_strategy("nonexistent")

    def test_get_strategy(self):
        engine = StrategyEngine()
        s = Strategy(id="s1", name="Test")
        engine.add_strategy(s)
        assert engine.get_strategy("s1").name == "Test"

    def test_plan_empty(self):
        engine = StrategyEngine()
        assert engine.plan() == []

    def test_plan_all_feasible(self):
        engine = StrategyEngine(ResourceBudget(cpu=100.0))
        engine.add_strategy(Strategy(id="s1", priority=1, resources=ResourceBudget(cpu=1.0)))
        engine.add_strategy(Strategy(id="s2", priority=5, resources=ResourceBudget(cpu=1.0)))
        plan = engine.plan()
        assert len(plan) == 2
        assert plan[0].priority == 5

    def test_release_custom_resources(self):
        """Test releasing custom resources via StrategyEngine deactivate."""
        engine = StrategyEngine(ResourceBudget(custom={"gpu": 4.0}))
        s = Strategy(id="s1", resources=ResourceBudget(custom={"gpu": 2.0}))
        engine.add_strategy(s)
        engine.activate("s1")
        engine.deactivate("s1")
        assert engine.available.custom["gpu"] == pytest.approx(4.0)


# ── priority.py coverage gaps ──────────────────────────────────
# Missing lines: 41-44, 61, 70-72, 76, 116


class TestTaskEdgeCases:
    def test_task_effective_score_within_hour(self):
        """Deadline < 1h: +20 boost (lines 41-44)."""
        t = Task(priority=Priority.MEDIUM, deadline=datetime.now() + timedelta(minutes=30))
        score = t.effective_score()
        assert score == pytest.approx(2.0 * 1.0 + 20.0)

    def test_task_effective_score_within_day(self):
        """Deadline < 1 day: +10 boost."""
        t = Task(priority=Priority.MEDIUM, deadline=datetime.now() + timedelta(hours=12))
        score = t.effective_score()
        assert score == pytest.approx(2.0 + 10.0)

    def test_task_effective_score_no_deadline(self):
        """No deadline: just base score."""
        t = Task(priority=Priority.HIGH, weight=2.0)
        assert t.effective_score() == pytest.approx(6.0)

    def test_task_effective_score_weight_applies_to_overdue(self):
        """Weight multiplies base even when overdue."""
        t = Task(priority=Priority.CRITICAL, weight=3.0,
                 deadline=datetime.now() - timedelta(hours=1))
        score = t.effective_score()
        assert score == pytest.approx(4.0 * 3.0 + 50.0)


class TestPriorityQueueEdgeCases:
    def test_remove_task(self):
        """Remove returns the task (line 61)."""
        pq = PriorityQueue()
        pq.add(Task(id="t1"))
        removed = pq.remove("t1")
        assert removed.id == "t1"
        assert pq.size == 0

    def test_remove_not_found(self):
        """Remove raises KeyError (line 70-72)."""
        pq = PriorityQueue()
        with pytest.raises(KeyError):
            pq.remove("nonexistent")

    def test_get_task(self):
        """Get returns task (line 76)."""
        pq = PriorityQueue()
        pq.add(Task(id="t1", title="Test"))
        assert pq.get("t1").title == "Test"

    def test_get_not_found(self):
        """Get raises KeyError for missing task."""
        pq = PriorityQueue()
        with pytest.raises(KeyError):
            pq.get("nonexistent")

    def test_complete_not_found(self):
        """Complete raises KeyError for missing task."""
        pq = PriorityQueue()
        with pytest.raises(KeyError):
            pq.complete("nonexistent")

    def test_peek_empty_queue(self):
        """Peek returns None when the queue is empty."""
        pq = PriorityQueue()
        assert pq.peek() is None

    def test_ordered_circular_dependency(self):
        """Ordered handles circular deps by picking highest score (line ~116)."""
        pq = PriorityQueue()
        pq.add(Task(id="a", priority=Priority.HIGH, dependencies=["b"]))
        pq.add(Task(id="b", priority=Priority.LOW, dependencies=["a"]))
        ordered = pq.ordered()
        assert len(ordered) == 2
        # Should break the cycle by picking highest score first
        assert ordered[0].id == "a"

    def test_overdue_empty(self):
        pq = PriorityQueue()
        assert pq.overdue() == []

    def test_due_within_empty(self):
        pq = PriorityQueue()
        assert pq.due_within(timedelta(hours=1)) == []

    def test_due_within_no_deadline(self):
        pq = PriorityQueue()
        pq.add(Task(id="t1"))
        assert pq.due_within(timedelta(hours=1)) == []

    def test_pop_with_deps_met(self):
        """Pop removes the highest-priority ready task."""
        pq = PriorityQueue()
        pq.add(Task(id="parent", priority=Priority.LOW))
        pq.add(Task(id="child", priority=Priority.HIGH, dependencies=["parent"]))
        first = pq.pop()
        assert first.id == "parent"
        second = pq.pop()
        assert second.id == "child"
        assert pq.pop() is None

    def test_tasks_property(self):
        pq = PriorityQueue()
        pq.add(Task(id="t1"))
        pq.add(Task(id="t2"))
        assert len(pq.tasks) == 2


# ── report.py coverage gaps ────────────────────────────────────
# Missing lines: 66, 73, 77, 114-115


class TestReportEdgeCases:
    def test_metric_equal_to_warning(self):
        """Value exactly at warning threshold is degraded (line 66)."""
        m = Metric(name="cpu", value=0.7, warning_threshold=0.7)
        assert m.status == HealthStatus.DEGRADED

    def test_metric_equal_to_critical(self):
        """Value exactly at critical threshold is critical (line 73)."""
        m = Metric(name="cpu", value=0.9, critical_threshold=0.9)
        assert m.status == HealthStatus.CRITICAL

    def test_metric_warning_only_no_critical(self):
        """Warning threshold only, no critical (line 77)."""
        m = Metric(name="lat", value=100.0, warning_threshold=50.0)
        assert m.status == HealthStatus.DEGRADED
        m2 = Metric(name="lat", value=40.0, warning_threshold=50.0)
        assert m2.status == HealthStatus.HEALTHY

    def test_auto_recommend_degraded(self):
        """Auto_recommend creates DEGRADED rec (line 114-115)."""
        r = StatusReport("test")
        r.add_metric(Metric("mem", 0.75, unit="%", warning_threshold=0.7, critical_threshold=0.9))
        recs = r.auto_recommend()
        assert len(recs) == 1
        assert recs[0].severity == HealthStatus.DEGRADED
        assert "mem" in recs[0].message

    def test_auto_recommend_all_healthy(self):
        """No recommendations when all metrics healthy."""
        r = StatusReport("test")
        r.add_metric(Metric("cpu", 0.3, warning_threshold=0.7, critical_threshold=0.9))
        recs = r.auto_recommend()
        assert len(recs) == 0

    def test_auto_recommend_mixed(self):
        """Mixed metrics produce multiple recommendations."""
        r = StatusReport("test")
        r.add_metric(Metric("ok", 0.3, warning_threshold=0.7, critical_threshold=0.9))
        r.add_metric(Metric("warn", 0.75, warning_threshold=0.7, critical_threshold=0.9))
        r.add_metric(Metric("crit", 0.95, warning_threshold=0.7, critical_threshold=0.9))
        recs = r.auto_recommend()
        assert len(recs) == 2  # warn + crit

    def test_get_metric(self):
        r = StatusReport()
        r.add_metric(Metric("x", 1.0))
        assert r.get_metric("x").value == 1.0

    def test_add_recommendation(self):
        r = StatusReport()
        rec = Recommendation(severity=HealthStatus.HEALTHY, message="All good")
        r.add_recommendation(rec)
        assert len(r.recommendations) == 1

    def test_summary_has_recommendations_count(self):
        r = StatusReport("svc")
        r.add_recommendation(Recommendation(severity=HealthStatus.HEALTHY, message="ok"))
        assert r.summary["recommendation_count"] == 1

    def test_health_all_critical(self):
        r = StatusReport()
        r.add_metric(Metric("a", 0.95, warning_threshold=0.7, critical_threshold=0.9))
        r.add_metric(Metric("b", 0.96, warning_threshold=0.7, critical_threshold=0.9))
        assert r.health == HealthStatus.CRITICAL

    def test_health_mixed_degraded_and_critical(self):
        r = StatusReport()
        r.add_metric(Metric("a", 0.75, warning_threshold=0.7, critical_threshold=0.9))
        r.add_metric(Metric("b", 0.95, warning_threshold=0.7, critical_threshold=0.9))
        assert r.health == HealthStatus.CRITICAL


# ── captain.py coverage gaps ───────────────────────────────────
# Missing lines: 83, 88, 124-127, 131


class TestCaptainEdgeCases:
    def test_decide_laissez_faire(self):
        """Laissez-faire picks last option (line 83)."""
        c = Captain(style=LeadershipStyle.LAISSEZ_FAIRE)
        d = c.decide("Pick", options=["a", "b", "c"])
        assert d.chosen == "c"

    def test_decide_situational_default(self):
        """Situational falls back to first option (line 88)."""
        c = Captain(style=LeadershipStyle.SITUATIONAL)
        d = c.decide("Pick", options=["a", "b", "c"])
        assert d.chosen == "a"

    def test_decide_preferred_out_of_range(self):
        """Preferred index out of range falls through to style logic (lines 124-127)."""
        c = Captain(style=LeadershipStyle.AUTOCRATIC)
        d = c.decide("Pick", options=["a", "b", "c"], preferred_idx=10)
        assert d.chosen == "a"  # autocratic picks first

    def test_decide_preferred_negative(self):
        """Negative preferred index falls through to style logic (line 131)."""
        c = Captain(style=LeadershipStyle.DEMOCRATIC)
        d = c.decide("Pick", options=["a", "b", "c"], preferred_idx=-1)
        assert d.chosen == "b"  # democratic picks middle

    def test_decide_records_decision(self):
        c = Captain()
        d = c.decide("Test", options=["a", "b"], rationale="because")
        assert len(c.decisions) == 1
        assert c.decisions[0].title == "Test"
        assert c.decisions[0].rationale == "because"

    def test_delegate_no_skills_match(self):
        """Delegate returns None when no member has the required skills."""
        c = Captain()
        c.add_member(TeamMember(id="1", name="A", skills=["python"]))
        result = c.delegate("task", required_skills=["rust"])
        assert result is None

    def test_delegate_increases_load(self):
        """Delegation increases the chosen member's load."""
        c = Captain()
        m = TeamMember(id="1", name="A", capacity=1.0, current_load=0.0)
        c.add_member(m)
        c.delegate("task")
        assert m.current_load == pytest.approx(0.1)

    def test_delegate_clamps_to_capacity(self):
        """Load is clamped to capacity."""
        c = Captain()
        m = TeamMember(id="1", name="A", capacity=0.05, current_load=0.0)
        c.add_member(m)
        c.delegate("task")
        assert m.current_load == pytest.approx(0.05)

    def test_release_below_zero_clamped(self):
        """Release clamps current_load to 0."""
        c = Captain()
        c.add_member(TeamMember(id="1", name="A", capacity=1.0, current_load=0.1))
        c.release("1", 0.5)
        assert c.get_member("1").current_load == pytest.approx(0.0)

    def test_get_member_not_found(self):
        c = Captain()
        with pytest.raises(KeyError):
            c.get_member("nonexistent")

    def test_decide_single_option(self):
        c = Captain(style=LeadershipStyle.DEMOCRATIC)
        d = c.decide("Pick", options=["only"])
        assert d.chosen == "only"

    def test_team_utilization_zero_capacity(self):
        """Utilization returns 0 when total capacity is 0."""
        c = Captain()
        c.add_member(TeamMember(id="1", name="A", capacity=0.0, current_load=0.0))
        assert c.team_utilization() == 0.0


# ── fleet.py coverage gaps ─────────────────────────────────────
# Missing lines: 41, 61, 66, 71


class TestFleetEdgeCases:
    def test_vessel_offline_capacity_zero(self):
        """Offline vessel has 0 available capacity (line 41)."""
        v = FleetVessel(status=VesselStatus.OFFLINE, capacity=2.0, current_load=0.0)
        assert v.available_capacity == 0.0

    def test_vessel_draining_capacity_zero(self):
        """Draining vessel has 0 available capacity."""
        v = FleetVessel(status=VesselStatus.DRAINING, capacity=2.0, current_load=0.0)
        assert v.available_capacity == 0.0

    def test_vessel_utilization_zero_capacity(self):
        """Utilization returns 0 when capacity is 0 (line 61)."""
        v = FleetVessel(capacity=0.0, current_load=1.0)
        assert v.utilization == 0.0

    def test_deregister_not_found(self):
        """Deregister raises KeyError (line 66)."""
        f = FleetCoordination()
        with pytest.raises(KeyError):
            f.deregister("nonexistent")

    def test_get_vessel_not_found(self):
        """Get vessel raises KeyError (line 71)."""
        f = FleetCoordination()
        with pytest.raises(KeyError):
            f.get_vessel("nonexistent")

    def test_assign_with_tags(self):
        """Assign filters by tags."""
        f = FleetCoordination()
        f.register(FleetVessel(id="v1", name="GPU box", tags=["gpu"], capacity=2.0))
        f.register(FleetVessel(id="v2", name="CPU box", tags=["cpu"], capacity=2.0))
        result = f.assign(tags=["gpu"])
        assert result.id == "v1"

    def test_assign_no_matching_tags(self):
        """Assign returns None when no vessels match tags."""
        f = FleetCoordination()
        f.register(FleetVessel(id="v1", tags=["cpu"]))
        assert f.assign(tags=["gpu"]) is None

    def test_assign_none_available(self):
        """Assign returns None when no vessel has enough capacity."""
        f = FleetCoordination()
        f.register(FleetVessel(id="v1", capacity=0.5, current_load=0.5))
        assert f.assign(load=0.1) is None

    def test_release_sets_idle(self):
        """Release below zero sets status to IDLE."""
        f = FleetCoordination()
        v = FleetVessel(id="v1", status=VesselStatus.BUSY, capacity=1.0, current_load=0.3)
        f.register(v)
        f.release("v1", 0.5)
        assert v.status == VesselStatus.IDLE

    def test_drain(self):
        """Drain sets status to DRAINING."""
        f = FleetCoordination()
        v = FleetVessel(id="v1", status=VesselStatus.IDLE)
        f.register(v)
        f.drain("v1")
        assert v.status == VesselStatus.DRAINING

    def test_healthy_vessels(self):
        f = FleetCoordination()
        f.register(FleetVessel(id="v1", status=VesselStatus.IDLE))
        f.register(FleetVessel(id="v2", status=VesselStatus.BUSY))
        f.register(FleetVessel(id="v3", status=VesselStatus.OFFLINE))
        assert len(f.healthy_vessels()) == 2

    def test_offline_vessels(self):
        f = FleetCoordination()
        f.register(FleetVessel(id="v1", status=VesselStatus.OFFLINE))
        f.register(FleetVessel(id="v2", status=VesselStatus.IDLE))
        assert len(f.offline_vessels()) == 1

    def test_fleet_utilization_empty(self):
        f = FleetCoordination()
        assert f.fleet_utilization() == 0.0

    def test_fleet_utilization_full(self):
        f = FleetCoordination()
        f.register(FleetVessel(id="v1", capacity=1.0, current_load=0.5))
        f.register(FleetVessel(id="v2", capacity=1.0, current_load=0.5))
        assert f.fleet_utilization() == pytest.approx(0.5)

    def test_vessel_busy_available_capacity(self):
        """Busy vessel still has available capacity if not fully loaded."""
        v = FleetVessel(status=VesselStatus.BUSY, capacity=2.0, current_load=0.5)
        assert v.available_capacity == pytest.approx(1.5)

    def test_vessel_idle_available_capacity(self):
        """Idle vessel has full capacity available."""
        v = FleetVessel(status=VesselStatus.IDLE, capacity=2.0, current_load=0.0)
        assert v.available_capacity == pytest.approx(2.0)

    def test_register_duplicate_raises(self):
        f = FleetCoordination()
        f.register(FleetVessel(id="v1"))
        with pytest.raises(ValueError):
            f.register(FleetVessel(id="v1"))
