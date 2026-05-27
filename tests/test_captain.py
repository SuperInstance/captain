"""Tests for captain.captain"""

import pytest
from captain.captain import Captain, LeadershipStyle, TeamMember


class TestTeamMember:
    def test_available_capacity(self):
        m = TeamMember(id="a", name="Alice", capacity=1.0, current_load=0.3)
        assert m.available_capacity == pytest.approx(0.7)

    def test_available_capacity_clamped(self):
        m = TeamMember(id="b", name="Bob", capacity=0.5, current_load=0.8)
        assert m.available_capacity == 0.0


class TestCaptain:
    def _make_captain(self):
        return Captain(name="Test", style=LeadershipStyle.SITUATIONAL)

    def test_add_and_get_member(self):
        c = self._make_captain()
        m = TeamMember(id="1", name="Alice", skills=["python"])
        c.add_member(m)
        assert c.team_size == 1
        assert c.get_member("1").name == "Alice"

    def test_add_duplicate_raises(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="A"))
        with pytest.raises(ValueError):
            c.add_member(TeamMember(id="1", name="B"))

    def test_remove_member(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="A"))
        removed = c.remove_member("1")
        assert removed.name == "A"
        assert c.team_size == 0

    def test_remove_missing_raises(self):
        c = self._make_captain()
        with pytest.raises(KeyError):
            c.remove_member("x")

    def test_team_full(self):
        c = Captain(max_team_size=2)
        c.add_member(TeamMember(id="1", name="A"))
        c.add_member(TeamMember(id="2", name="B"))
        with pytest.raises(ValueError):
            c.add_member(TeamMember(id="3", name="C"))

    def test_decide_autocratic(self):
        c = Captain(style=LeadershipStyle.AUTOCRATIC)
        d = c.decide("Pick", options=["a", "b", "c"])
        assert d.chosen == "a"

    def test_decide_democratic(self):
        c = Captain(style=LeadershipStyle.DEMOCRATIC)
        d = c.decide("Pick", options=["a", "b", "c"])
        assert d.chosen == "b"

    def test_decide_preferred(self):
        c = self._make_captain()
        d = c.decide("Pick", options=["a", "b", "c"], preferred_idx=2)
        assert d.chosen == "c"

    def test_decide_empty_options_raises(self):
        c = self._make_captain()
        with pytest.raises(ValueError):
            c.decide("Empty", options=[])

    def test_delegate_prefers_available(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="Busy", capacity=1.0, current_load=0.9))
        c.add_member(TeamMember(id="2", name="Free", capacity=1.0, current_load=0.1))
        result = c.delegate("task")
        assert result.name == "Free"

    def test_delegate_with_skills(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="Dev", skills=["python"]))
        c.add_member(TeamMember(id="2", name="Ops", skills=["linux"]))
        result = c.delegate("task", required_skills=["python"])
        assert result.name == "Dev"

    def test_delegate_none_when_full(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="Full", capacity=1.0, current_load=1.0))
        assert c.delegate("task") is None

    def test_team_utilization(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="A", capacity=1.0, current_load=0.5))
        assert c.team_utilization() == pytest.approx(0.5)

    def test_team_utilization_empty(self):
        c = self._make_captain()
        assert c.team_utilization() == 0.0

    def test_release(self):
        c = self._make_captain()
        c.add_member(TeamMember(id="1", name="A", capacity=1.0, current_load=0.5))
        c.release("1", 0.2)
        assert c.get_member("1").current_load == pytest.approx(0.3)
