"""Tests for the evaluation framework."""

from evaluations.evaluation_framework import (
    Experiment,
    ExperimentRunner,
    MetricCollector,
)


def test_metric_collector_records_and_summarises():
    collector = MetricCollector()
    collector.record("latency", 10.0, unit="ms")
    collector.record("latency", 20.0, unit="ms")
    collector.record("latency", 30.0, unit="ms")

    summaries = collector.summary()
    assert len(summaries) == 1
    s = summaries[0]
    assert s.name == "latency"
    assert s.count == 3
    assert s.mean == 20.0
    assert s.unit == "ms"


def test_metric_collector_multiple_metrics():
    collector = MetricCollector()
    collector.record("a", 1.0)
    collector.record("b", 2.0)
    assert set(collector.metric_names) == {"a", "b"}


class _DummyExperiment(Experiment):
    name = "dummy"
    description = "A test experiment"

    def run(self, collector: MetricCollector) -> None:
        collector.record("value", 42.0)


class _FailingExperiment(Experiment):
    name = "failing"
    description = "An experiment that always fails"

    def run(self, collector: MetricCollector) -> None:
        raise RuntimeError("intentional failure")


def test_runner_executes_experiment():
    runner = ExperimentRunner([_DummyExperiment()])
    results = runner.run_all()
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].metrics[0].mean == 42.0


def test_runner_handles_failure():
    runner = ExperimentRunner([_FailingExperiment()])
    results = runner.run_all()
    assert len(results) == 1
    assert results[0].success is False
    assert "intentional failure" in (results[0].error or "")
