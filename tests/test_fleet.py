"""Tests for captain.fleet"""

import pytest
from captain.fleet import FleetCoordination, FleetVessel, VesselStatus


class TestFleetVessel:
    def test_available_capacity_idle(self):
        v = FleetVessel(capacity=1.0, current_load=0.3)
        assert v.available_capacity == pytest.approx(0.7)

    def test_available_capacity_offline(self):
        v = FleetVessel(status=VesselStatus.OFFLINE, capacity=1.0, current_load=0.0)
        assert v.available_capacity == 0.0

    def test_utilization(self):
        v = FleetVessel(capacity=2.0, current_load=1.0)
        assert v.utilization == pytest.approx(0.5)


class TestFleetCoordination:
    def _make_fleet(self, n: int = 3) -> FleetCoordination:
        fleet = FleetCoordination(name="test")
        for i in range(n):
            fleet.register(FleetVessel(id=f"v{i}", name=f"Vessel-{i}", capacity=1.0))
        return fleet

    def test_register_and_size(self):
        fleet = self._make_fleet(3)
        assert fleet.size == 3

    def test_register_duplicate_raises(self):
        fleet = FleetCoordination()
        fleet.register(FleetVessel(id="v1"))
        with pytest.raises(ValueError):
            fleet.register(FleetVessel(id="v1"))

    def test_deregister(self):
        fleet = self._make_fleet(2)
        fleet.deregister("v0")
        assert fleet.size == 1

    def test_assign_least_loaded(self):
        fleet = self._make_fleet(3)
        fleet.get_vessel("v0").current_load = 0.5
        fleet.get_vessel("v1").current_load = 0.1
        fleet.get_vessel("v2").current_load = 0.8
        v = fleet.assign(0.1)
        assert v.id == "v1"

    def test_assign_with_tags(self):
        fleet = FleetCoordination()
        fleet.register(FleetVessel(id="v0", tags=["gpu"]))
        fleet.register(FleetVessel(id="v1", tags=["cpu"]))
        v = fleet.assign(tags=["gpu"])
        assert v.id == "v0"

    def test_assign_none_when_full(self):
        fleet = FleetCoordination()
        fleet.register(FleetVessel(id="v0", capacity=0.5, current_load=0.5))
        assert fleet.assign(0.1) is None

    def test_release(self):
        fleet = self._make_fleet(1)
        fleet.get_vessel("v0").current_load = 0.5
        fleet.release("v0", 0.5)
        assert fleet.get_vessel("v0").status == VesselStatus.IDLE

    def test_drain(self):
        fleet = self._make_fleet(1)
        fleet.drain("v0")
        assert fleet.get_vessel("v0").status == VesselStatus.DRAINING

    def test_fleet_utilization(self):
        fleet = self._make_fleet(2)
        fleet.get_vessel("v0").current_load = 0.5
        fleet.get_vessel("v1").current_load = 0.5
        assert fleet.fleet_utilization() == pytest.approx(0.5)

    def test_healthy_and_offline(self):
        fleet = FleetCoordination()
        fleet.register(FleetVessel(id="v0", status=VesselStatus.IDLE))
        fleet.register(FleetVessel(id="v1", status=VesselStatus.OFFLINE))
        assert len(fleet.healthy_vessels()) == 1
        assert len(fleet.offline_vessels()) == 1
