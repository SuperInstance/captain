# captain — Team Leadership & Fleet Coordination

Captain agents for the Cocapn multi-agent system — team leadership, task prioritization, and fleet coordination.

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from captain import Captain, LeadershipStyle, TeamMember

# Create a captain
captain = Captain(name="Leia", style=LeadershipStyle.SITUATIONAL)

# Build a team
captain.add_member(TeamMember(id="1", name="Alice", skills=["python", "ml"], capacity=1.0))
captain.add_member(TeamMember(id="2", name="Bob", skills=["rust", "systems"], capacity=1.0))

# Delegate work
assignee = captain.delegate("train model", required_skills=["ml"])
print(f"Assigned to: {assignee.name}")  # Alice

# Make decisions
decision = captain.decide("Deploy strategy", options=["rolling", "blue-green", "canary"])
print(f"Chose: {decision.chosen}")
```

## Fleet Coordination

```python
from captain import FleetCoordination, FleetVessel

fleet = FleetCoordination(name="production")
fleet.register(FleetVessel(id="v1", name="worker-1", capacity=2.0, tags=["gpu"]))
fleet.register(FleetVessel(id="v2", name="worker-2", capacity=1.0, tags=["cpu"]))

# Assign work to the least-loaded vessel
vessel = fleet.assign(0.5, tags=["gpu"])
print(f"Work assigned to: {vessel.name}")

print(f"Fleet utilization: {fleet.fleet_utilization():.0%}")
```

## Priority Queue

```python
from datetime import datetime, timedelta
from captain import PriorityQueue, Task, Priority

pq = PriorityQueue()
pq.add(Task(id="hotfix", title="Fix login bug", priority=Priority.CRITICAL,
            deadline=datetime.now() + timedelta(hours=2)))
pq.add(Task(id="feature", title="Add dark mode", priority=Priority.LOW,
            dependencies=["hotfix"]))

# Dependencies are respected — hotfix comes first
next_task = pq.peek()
print(f"Next up: {next_task.title}")  # Fix login bug
```

## Strategy Engine

```python
from captain import StrategyEngine, Strategy, ResourceBudget

engine = StrategyEngine(ResourceBudget(cpu=8.0, memory=32.0, budget=500.0))
engine.add_strategy(Strategy(id="s1", name="Expand CDN", priority=10,
                             resources=ResourceBudget(cpu=2.0, memory=8.0, budget=100.0)))
engine.add_strategy(Strategy(id="s2", name="ML Pipeline", priority=5,
                             resources=ResourceBudget(cpu=4.0, memory=16.0, budget=200.0)))

plan = engine.plan()  # Ordered by priority, filtered by feasibility
engine.activate(plan[0].id)
```

## Status Reports

```python
from captain import StatusReport, Metric

report = StatusReport("api-server")
report.add_metric(Metric("cpu", 0.85, unit="%", warning_threshold=0.7, critical_threshold=0.9))
report.add_metric(Metric("latency_p99", 120.0, unit="ms", warning_threshold=100.0))

print(f"Health: {report.health.value}")  # degraded

recs = report.auto_recommend()
for r in recs:
    print(f"[{r.severity.value}] {r.message}")
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## License

MIT
