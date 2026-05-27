"""Captain class — team leadership and decision making."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class LeadershipStyle(enum.Enum):
    """Leadership styles a Captain can adopt."""

    DEMOCRATIC = "democratic"
    AUTOCRATIC = "autocratic"
    LAISSEZ_FAIRE = "laissez_faire"
    SITUATIONAL = "situational"


@dataclass
class TeamMember:
    """A member of the captain's team."""

    id: str
    name: str
    skills: list[str] = field(default_factory=list)
    capacity: float = 1.0  # 0.0–1.0
    current_load: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available_capacity(self) -> float:
        return max(0.0, self.capacity - self.current_load)


@dataclass
class Decision:
    """A decision made by the Captain."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    rationale: str = ""
    options: list[str] = field(default_factory=list)
    chosen: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class Captain:
    """Team leader responsible for coordination, delegation, and decision making."""

    def __init__(
        self,
        name: str = "Captain",
        style: LeadershipStyle = LeadershipStyle.SITUATIONAL,
        max_team_size: int = 10,
    ) -> None:
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.style = style
        self.max_team_size = max_team_size
        self._team: dict[str, TeamMember] = {}
        self._decisions: list[Decision] = []
        self._delegation_history: list[dict[str, Any]] = []

    # --- team management ---

    def add_member(self, member: TeamMember) -> None:
        if len(self._team) >= self.max_team_size:
            raise ValueError(f"Team is full (max {self.max_team_size})")
        if member.id in self._team:
            raise ValueError(f"Member {member.id} already exists")
        self._team[member.id] = member

    def remove_member(self, member_id: str) -> TeamMember:
        if member_id not in self._team:
            raise KeyError(f"No member with id {member_id}")
        return self._team.pop(member_id)

    def get_member(self, member_id: str) -> TeamMember:
        if member_id not in self._team:
            raise KeyError(f"No member with id {member_id}")
        return self._team[member_id]

    @property
    def team(self) -> list[TeamMember]:
        return list(self._team.values())

    @property
    def team_size(self) -> int:
        return len(self._team)

    # --- decision making ---

    def decide(
        self,
        title: str,
        options: list[str],
        rationale: str = "",
        *,
        preferred_idx: int | None = None,
    ) -> Decision:
        chosen = self._pick_option(options, preferred_idx)
        decision = Decision(
            title=title,
            rationale=rationale,
            options=options,
            chosen=chosen,
        )
        self._decisions.append(decision)
        return decision

    def _pick_option(self, options: list[str], preferred: int | None) -> str:
        if not options:
            raise ValueError("Must provide at least one option")
        if preferred is not None and 0 <= preferred < len(options):
            return options[preferred]
        match self.style:
            case LeadershipStyle.AUTOCRATIC:
                return options[0]
            case LeadershipStyle.DEMOCRATIC:
                return options[len(options) // 2]
            case LeadershipStyle.LAISSEZ_FAIRE:
                return options[-1]
            case _:
                return options[0]

    @property
    def decisions(self) -> list[Decision]:
        return list(self._decisions)

    # --- delegation ---

    def delegate(self, task_name: str, required_skills: list[str] | None = None) -> TeamMember | None:
        candidates = self._team.values()
        if required_skills:
            candidates = [
                m for m in candidates if any(s in m.skills for s in required_skills)
            ]
        candidates = sorted(candidates, key=lambda m: m.available_capacity, reverse=True)
        if not candidates or candidates[0].available_capacity <= 0:
            return None
        member = candidates[0]
        member.current_load = min(member.capacity, member.current_load + 0.1)
        self._delegation_history.append(
            {"task": task_name, "member_id": member.id, "timestamp": datetime.now()}
        )
        return member

    def release(self, member_id: str, load_amount: float = 0.1) -> None:
        member = self.get_member(member_id)
        member.current_load = max(0.0, member.current_load - load_amount)

    # --- status ---

    def team_utilization(self) -> float:
        if not self._team:
            return 0.0
        total = sum(m.capacity for m in self._team.values())
        loaded = sum(m.current_load for m in self._team.values())
        return loaded / total if total > 0 else 0.0
