# captain — Fleet Commanding Vessel

**Team leadership, task prioritization, strategy selection, and fleet coordination for multi-agent systems.**

## What This Gives You

- **Priority queues** — weighted task prioritization with deadline tracking and dynamic reordering
- **Strategy engine** — select and apply coordination strategies (sequential, parallel, adaptive) based on task requirements
- **Fleet coordination** — assign vessels to tasks, track availability, balance workloads
- **Leadership styles** — configurable leadership modes (directive, collaborative, delegative) that affect task distribution
- **Status reports** — structured fleet health reports with metrics, health status, and trend data

## Quick Start

```bash
pip install captain
```

```python
from captain import Captain, LeadershipStyle, Task, Priority

# Create a captain with a leadership style
captain = Captain(name="fleet-captain", style=LeadershipStyle.ADAPTIVE)

# Add fleet vessels
from captain import FleetVessel, FleetCoordination
coord = FleetCoordination()
coord.register(FleetVessel(id="agent-1", capabilities=["rust", "benchmarking"]))
coord.register(FleetVessel(id="agent-2", capabilities=["python", "docs"]))

# Create and prioritize tasks
task = Task(title="Rewrite README", priority=Priority.HIGH, deadline="2026-06-01")
captain.assign(task, fleet=coord)

# Run strategy
from captain import StrategyEngine, Strategy, ResourceBudget
engine = StrategyEngine()
plan = engine.plan(tasks=captain.pending_tasks, fleet=coord, budget=ResourceBudget(max_agents=5))
print(plan)

# Get status report
report = captain.report()
print(f"Fleet health: {report.health}")
print(f"Tasks in progress: {report.metrics.tasks_in_progress}")
```

## API Reference

### `Captain(name, style=ADAPTIVE)`
### `LeadershipStyle` — `DIRECTIVE`, `COLLABORATIVE`, `DELEGATIVE`, `ADAPTIVE`
### `Task(title, priority, deadline, requirements)`
### `Priority` — `LOW`, `NORMAL`, `HIGH`, `CRITICAL`
### `PriorityQueue` — Weighted, deadline-aware task queue
### `FleetCoordination` — Register vessels, assign tasks, track availability
### `FleetVessel(id, capabilities, status)`
### `StrategyEngine` / `Strategy` / `ResourceBudget`
### `StatusReport` / `HealthStatus` / `Metric`

## How It Fits

The commanding vessel of the [SuperInstance fleet](https://github.com/SuperInstance). Receives dispatched work from [Co-Captain](https://github.com/SuperInstance/co-captain-git-agent) and distributes it across fleet agents.

- **[co-captain-git-agent](https://github.com/SuperInstance/co-captain-git-agent)** — Human liaison (dispatches to captain)
- **[cocapn-com](https://github.com/SuperInstance/cocapn-com)** — Inter-agent messaging
- **[cluster-orchestrator](https://github.com/SuperInstance/cluster-orchestrator)** — Cluster-level orchestration
- **[fleet-health-monitor](https://github.com/SuperInstance/fleet-health-monitor)** — Fleet health daemon

## Testing

```bash
pytest tests/
```

## Installation

```bash
pip install captain
```

Python 3.10+. MIT license.
