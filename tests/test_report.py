"""Tests for captain.report"""

import pytest
from captain.report import HealthStatus, Metric, Recommendation, StatusReport


class TestMetric:
    def test_healthy(self):
        m = Metric(name="cpu", value=0.3, warning_threshold=0.7, critical_threshold=0.9)
        assert m.status == HealthStatus.HEALTHY

    def test_degraded(self):
        m = Metric(name="cpu", value=0.75, warning_threshold=0.7, critical_threshold=0.9)
        assert m.status == HealthStatus.DEGRADED

    def test_critical(self):
        m = Metric(name="cpu", value=0.95, warning_threshold=0.7, critical_threshold=0.9)
        assert m.status == HealthStatus.CRITICAL

    def test_no_thresholds(self):
        m = Metric(name="x", value=999.0)
        assert m.status == HealthStatus.HEALTHY


class TestStatusReport:
    def test_health_reflects_worst_metric(self):
        r = StatusReport("test")
        r.add_metric(Metric("cpu", 0.3, warning_threshold=0.7))
        r.add_metric(Metric("mem", 0.8, warning_threshold=0.7))
        assert r.health == HealthStatus.DEGRADED

    def test_unknown_when_empty(self):
        r = StatusReport()
        assert r.health == HealthStatus.UNKNOWN

    def test_auto_recommend(self):
        r = StatusReport("test")
        r.add_metric(Metric("disk", 0.95, unit="%", warning_threshold=0.8, critical_threshold=0.9))
        recs = r.auto_recommend()
        assert len(recs) == 1
        assert recs[0].severity == HealthStatus.CRITICAL

    def test_summary(self):
        r = StatusReport("svc")
        r.add_metric(Metric("latency", 42.0, unit="ms"))
        s = r.summary
        assert s["health"] == "healthy"
        assert s["metric_count"] == 1

    def test_add_remove_metric(self):
        r = StatusReport()
        r.add_metric(Metric("x", 1.0))
        assert len(r.metrics) == 1
        r.remove_metric("x")
        assert len(r.metrics) == 0

    def test_remove_missing_raises(self):
        r = StatusReport()
        with pytest.raises(KeyError):
            r.remove_metric("nope")
