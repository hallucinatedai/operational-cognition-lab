"""Base evaluation framework for running and measuring experiments.

Provides an Experiment base class, metric collection, and a runner that
executes experiments with consistent lifecycle and reporting.
"""

from __future__ import annotations

import argparse
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class Metric:
    """A single recorded metric value."""

    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)


class MetricCollector:
    """Collects and aggregates metric observations during an experiment."""

    def __init__(self) -> None:
        self._metrics: dict[str, list[float]] = {}
        self._units: dict[str, str] = {}

    def record(self, name: str, value: float, unit: str = "") -> None:
        self._metrics.setdefault(name, []).append(value)
        if unit:
            self._units[name] = unit

    def summary(self) -> list[MetricSummary]:
        results: list[MetricSummary] = []
        for name, values in self._metrics.items():
            arr = np.array(values)
            results.append(
                MetricSummary(
                    name=name,
                    count=len(values),
                    mean=float(np.mean(arr)),
                    std=float(np.std(arr)),
                    min_val=float(np.min(arr)),
                    max_val=float(np.max(arr)),
                    p50=float(np.percentile(arr, 50)),
                    p95=float(np.percentile(arr, 95)),
                    unit=self._units.get(name, ""),
                )
            )
        return results

    @property
    def metric_names(self) -> list[str]:
        return list(self._metrics.keys())


@dataclass
class MetricSummary:
    name: str
    count: int
    mean: float
    std: float
    min_val: float
    max_val: float
    p50: float
    p95: float
    unit: str = ""


# ---------------------------------------------------------------------------
# Experiment base class
# ---------------------------------------------------------------------------


class Experiment(ABC):
    """Base class for all experiments in the lab."""

    name: str = "unnamed"
    description: str = ""

    def setup(self) -> None:
        """Prepare resources needed for the experiment."""

    @abstractmethod
    def run(self, collector: MetricCollector) -> None:
        """Execute the experiment logic and record metrics."""
        ...

    def teardown(self) -> None:
        """Clean up resources after the experiment."""


@dataclass
class ExperimentResult:
    experiment_name: str
    description: str
    duration_seconds: float
    metrics: list[MetricSummary]
    success: bool
    error: str | None = None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class ExperimentRunner:
    """Executes experiments with lifecycle management and reporting."""

    def __init__(self, experiments: list[Experiment] | None = None) -> None:
        self._experiments: list[Experiment] = experiments or []
        self._results: list[ExperimentResult] = []

    def register(self, experiment: Experiment) -> None:
        self._experiments.append(experiment)

    def run_all(self) -> list[ExperimentResult]:
        self._results = []
        for experiment in self._experiments:
            result = self._run_one(experiment)
            self._results.append(result)
        return self._results

    def _run_one(self, experiment: Experiment) -> ExperimentResult:
        console.print(f"\n[bold cyan]Running: {experiment.name}[/bold cyan]")
        console.print(f"  {experiment.description}")

        collector = MetricCollector()
        error: str | None = None
        success = True

        try:
            experiment.setup()
            t0 = time.perf_counter()
            experiment.run(collector)
            duration = time.perf_counter() - t0
        except Exception as exc:
            duration = 0.0
            error = str(exc)
            success = False
        finally:
            try:
                experiment.teardown()
            except Exception:
                pass

        return ExperimentResult(
            experiment_name=experiment.name,
            description=experiment.description,
            duration_seconds=duration,
            metrics=collector.summary(),
            success=success,
            error=error,
        )

    def print_report(self) -> None:
        console.rule("[bold blue]Experiment Evaluation Report")

        for result in self._results:
            status = "[bold green]PASS[/]" if result.success else "[bold red]FAIL[/]"
            console.print(
                f"\n{status} [bold]{result.experiment_name}[/bold] ({result.duration_seconds:.3f}s)"
            )

            if result.error:
                console.print(f"  [red]Error: {result.error}[/red]")
                continue

            if not result.metrics:
                console.print("  [dim]No metrics recorded[/dim]")
                continue

            table = Table(show_header=True)
            table.add_column("Metric")
            table.add_column("Mean", justify="right")
            table.add_column("Std", justify="right")
            table.add_column("Min", justify="right")
            table.add_column("Max", justify="right")
            table.add_column("P50", justify="right")
            table.add_column("P95", justify="right")
            table.add_column("N", justify="right")

            for m in result.metrics:
                unit_suffix = f" {m.unit}" if m.unit else ""
                table.add_row(
                    m.name,
                    f"{m.mean:.4f}{unit_suffix}",
                    f"{m.std:.4f}",
                    f"{m.min_val:.4f}",
                    f"{m.max_val:.4f}",
                    f"{m.p50:.4f}",
                    f"{m.p95:.4f}",
                    str(m.count),
                )
            console.print(table)


# ---------------------------------------------------------------------------
# Demo experiments
# ---------------------------------------------------------------------------


class LatencyExperiment(Experiment):
    name = "latency-baseline"
    description = "Measure baseline processing latency for simulated workloads"

    def run(self, collector: MetricCollector) -> None:
        rng = np.random.default_rng(42)
        for _ in range(200):
            latency = rng.exponential(scale=15.0)
            collector.record("latency_ms", latency, unit="ms")
            throughput = 1000 / max(latency, 0.1)
            collector.record("throughput_rps", throughput, unit="req/s")


class AccuracyExperiment(Experiment):
    name = "classification-accuracy"
    description = "Evaluate classification accuracy on synthetic labelled data"

    def run(self, collector: MetricCollector) -> None:
        rng = np.random.default_rng(99)
        for _ in range(100):
            accuracy = rng.beta(8, 2)
            collector.record("accuracy", accuracy)
            f1 = rng.beta(7, 3)
            collector.record("f1_score", f1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluation framework demo")
    parser.parse_args(argv)

    runner = ExperimentRunner()
    runner.register(LatencyExperiment())
    runner.register(AccuracyExperiment())

    runner.run_all()
    runner.print_report()
    console.print("\n[bold green]Evaluation complete.[/]")


if __name__ == "__main__":
    main()
