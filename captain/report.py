"""StatusReport — metrics, health, and recommendations."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class HealthStatus(enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """A named metric with a numeric value and optional thresholds."""

    name: str
    value: float
    unit: str = ""
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> HealthStatus:
        if self.critical_threshold is not None and self.value >= self.critical_threshold:
            return HealthStatus.CRITICAL
        if self.warning_threshold is not None and self.value >= self.warning_threshold:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY


@dataclass
class Recommendation:
    """An actionable recommendation."""

    severity: HealthStatus
    message: str
    action: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class StatusReport:
    """Aggregates metrics into a health report with recommendations."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self.timestamp = datetime.now()
        self._metrics: dict[str, Metric] = {}
        self._recommendations: list[Recommendation] = []

    def add_metric(self, metric: Metric) -> None:
        self._metrics[metric.name] = metric

    def remove_metric(self, name: str) -> Metric:
        if name not in self._metrics:
            raise KeyError(f"No metric {name}")
        return self._metrics.pop(name)

    def get_metric(self, name: str) -> Metric:
        return self._metrics[name]

    @property
    def metrics(self) -> list[Metric]:
        return list(self._metrics.values())

    def add_recommendation(self, rec: Recommendation) -> None:
        self._recommendations.append(rec)

    @property
    def recommendations(self) -> list[Recommendation]:
        return list(self._recommendations)

    # --- overall health ---

    @property
    def health(self) -> HealthStatus:
        if not self._metrics:
            return HealthStatus.UNKNOWN
        worst = HealthStatus.HEALTHY
        order = {HealthStatus.HEALTHY: 0, HealthStatus.DEGRADED: 1, HealthStatus.CRITICAL: 2}
        for m in self._metrics.values():
            s = m.status
            if order.get(s, 0) > order.get(worst, 0):
                worst = s
        return worst

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "health": self.health.value,
            "metric_count": len(self._metrics),
            "recommendation_count": len(self._recommendations),
            "metrics": {m.name: {"value": m.value, "status": m.status.value} for m in self._metrics.values()},
        }

    def auto_recommend(self) -> list[Recommendation]:
        """Generate recommendations from metrics that cross thresholds."""
        recs: list[Recommendation] = []
        for m in self._metrics.values():
            if m.status == HealthStatus.CRITICAL:
                recs.append(Recommendation(
                    severity=HealthStatus.CRITICAL,
                    message=f"Metric '{m.name}' is critical: {m.value}{m.unit}",
                    action=f"Investigate and address {m.name} immediately",
                ))
            elif m.status == HealthStatus.DEGRADED:
                recs.append(Recommendation(
                    severity=HealthStatus.DEGRADED,
                    message=f"Metric '{m.name}' is degraded: {m.value}{m.unit}",
                    action=f"Monitor {m.name} and plan remediation",
                ))
        self._recommendations.extend(recs)
        return recs
