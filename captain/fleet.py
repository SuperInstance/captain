"""FleetCoordination — multi-agent deployments and load balancing."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class VesselStatus(enum.Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    DRAINING = "draining"


@dataclass
class FleetVessel:
    """A single vessel (agent) in the fleet."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    status: VesselStatus = VesselStatus.IDLE
    capacity: float = 1.0
    current_load: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime | None = None

    @property
    def available_capacity(self) -> float:
        if self.status != VesselStatus.IDLE and self.status != VesselStatus.BUSY:
            return 0.0
        return max(0.0, self.capacity - self.current_load)

    @property
    def utilization(self) -> float:
        if self.capacity <= 0:
            return 0.0
        return self.current_load / self.capacity


class FleetCoordination:
    """Manages a fleet of vessels — deployment, load balancing, and health."""

    def __init__(self, name: str = "default-fleet") -> None:
        self.name = name
        self._vessels: dict[str, FleetVessel] = {}

    # --- vessel management ---

    def register(self, vessel: FleetVessel) -> None:
        if vessel.id in self._vessels:
            raise ValueError(f"Vessel {vessel.id} already registered")
        self._vessels[vessel.id] = vessel

    def deregister(self, vessel_id: str) -> FleetVessel:
        if vessel_id not in self._vessels:
            raise KeyError(f"No vessel {vessel_id}")
        return self._vessels.pop(vessel_id)

    def get_vessel(self, vessel_id: str) -> FleetVessel:
        if vessel_id not in self._vessels:
            raise KeyError(f"No vessel {vessel_id}")
        return self._vessels[vessel_id]

    @property
    def vessels(self) -> list[FleetVessel]:
        return list(self._vessels.values())

    @property
    def size(self) -> int:
        return len(self._vessels)

    # --- load balancing ---

    def assign(self, load: float = 0.1, *, tags: list[str] | None = None) -> FleetVessel | None:
        """Assign work to the best-available vessel (least-loaded first)."""
        candidates = [v for v in self._vessels.values() if v.available_capacity >= load]
        if tags:
            candidates = [v for v in candidates if any(t in v.tags for t in tags)]
        if not candidates:
            return None
        candidates.sort(key=lambda v: v.current_load / v.capacity if v.capacity else 0.0)
        vessel = candidates[0]
        vessel.current_load = min(vessel.capacity, vessel.current_load + load)
        vessel.status = VesselStatus.BUSY if vessel.available_capacity <= 0 else VesselStatus.BUSY
        return vessel

    def release(self, vessel_id: str, load: float = 0.1) -> None:
        vessel = self.get_vessel(vessel_id)
        vessel.current_load = max(0.0, vessel.current_load - load)
        if vessel.current_load <= 0:
            vessel.status = VesselStatus.IDLE

    def drain(self, vessel_id: str) -> None:
        """Mark a vessel as draining — no new assignments."""
        vessel = self.get_vessel(vessel_id)
        vessel.status = VesselStatus.DRAINING

    # --- fleet metrics ---

    def total_capacity(self) -> float:
        return sum(v.capacity for v in self._vessels.values())

    def total_load(self) -> float:
        return sum(v.current_load for v in self._vessels.values())

    def fleet_utilization(self) -> float:
        cap = self.total_capacity()
        return self.total_load() / cap if cap > 0 else 0.0

    def healthy_vessels(self) -> list[FleetVessel]:
        return [v for v in self._vessels.values() if v.status in (VesselStatus.IDLE, VesselStatus.BUSY)]

    def offline_vessels(self) -> list[FleetVessel]:
        return [v for v in self._vessels.values() if v.status == VesselStatus.OFFLINE]
