"""Detect recurring patterns in workflow execution data.

Uses K-Means clustering to group similar workflow executions, scores anomalies
based on distance from cluster centroids, and tracks how patterns evolve over
time windows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

console = Console()


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_synthetic_workflows(
    n_samples: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Create synthetic workflow execution data with three natural clusters."""
    rng = np.random.default_rng(seed)

    clusters: list[dict[str, tuple[float, float]]] = [
        {
            "step_count": (10, 2),
            "duration_seconds": (30, 5),
            "failure_rate": (0.02, 0.01),
            "retry_count": (0, 0.5),
        },
        {
            "step_count": (25, 5),
            "duration_seconds": (120, 20),
            "failure_rate": (0.10, 0.04),
            "retry_count": (2, 1),
        },
        {
            "step_count": (50, 8),
            "duration_seconds": (300, 40),
            "failure_rate": (0.25, 0.08),
            "retry_count": (5, 2),
        },
    ]

    rows: list[dict] = []
    base_time = datetime(2025, 1, 1)
    n_clusters = len(clusters)
    samples_per_cluster = n_samples // n_clusters
    remainder = n_samples % n_clusters

    for idx, cluster_def in enumerate(clusters):
        count = samples_per_cluster + (1 if idx < remainder else 0)
        for i in range(count):
            row: dict = {}
            for feat, (mean, std) in cluster_def.items():
                value = rng.normal(mean, std)
                if feat in ("step_count", "retry_count"):
                    value = max(0, int(round(value)))
                elif feat == "failure_rate":
                    value = float(np.clip(value, 0.0, 1.0))
                else:
                    value = max(0.0, float(value))
                row[feat] = value
            row["workflow_id"] = f"wf-{len(rows):04d}"
            row["timestamp"] = base_time + timedelta(hours=int(rng.integers(0, 24 * 90)))
            rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

FEATURE_COLUMNS = ["step_count", "duration_seconds", "failure_rate", "retry_count"]


@dataclass
class PatternDetectionResult:
    """Container for clustering + anomaly detection outputs."""

    data: pd.DataFrame
    n_clusters: int
    cluster_centers: np.ndarray
    anomaly_threshold: float
    anomaly_count: int
    cluster_summary: pd.DataFrame
    trend_summary: pd.DataFrame | None = None
    _feature_cols: list[str] = field(default_factory=lambda: list(FEATURE_COLUMNS))


def detect_patterns(
    df: pd.DataFrame,
    n_clusters: int = 3,
    anomaly_percentile: float = 95.0,
) -> PatternDetectionResult:
    """Run pattern detection pipeline on workflow data."""
    features = df[FEATURE_COLUMNS].values
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    model = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = model.fit_predict(scaled)

    distances = np.linalg.norm(scaled - model.cluster_centers_[labels], axis=1)
    threshold = float(np.percentile(distances, anomaly_percentile))
    anomalies = distances > threshold

    df = df.copy()
    df["cluster"] = labels
    df["anomaly_score"] = distances
    df["is_anomaly"] = anomalies

    cluster_summary = (
        df.groupby("cluster")[FEATURE_COLUMNS]
        .agg(["mean", "std", "count"])
    )

    trend = None
    if "timestamp" in df.columns:
        df["period"] = pd.to_datetime(df["timestamp"]).dt.to_period("W")
        trend = (
            df.groupby(["period", "cluster"])
            .size()
            .unstack(fill_value=0)
        )

    return PatternDetectionResult(
        data=df,
        n_clusters=n_clusters,
        cluster_centers=model.cluster_centers_,
        anomaly_threshold=threshold,
        anomaly_count=int(anomalies.sum()),
        cluster_summary=cluster_summary,
        trend_summary=trend,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(result: PatternDetectionResult) -> None:
    """Pretty-print the detection results."""
    console.rule("[bold blue]Workflow Pattern Detection Report")

    # Cluster overview
    table = Table(title="Cluster Overview")
    table.add_column("Cluster", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Avg Steps", justify="right")
    table.add_column("Avg Duration (s)", justify="right")
    table.add_column("Avg Failure Rate", justify="right")
    table.add_column("Avg Retries", justify="right")

    for cluster_id in range(result.n_clusters):
        subset = result.data[result.data["cluster"] == cluster_id]
        table.add_row(
            str(cluster_id),
            str(len(subset)),
            f"{subset['step_count'].mean():.1f}",
            f"{subset['duration_seconds'].mean():.1f}",
            f"{subset['failure_rate'].mean():.3f}",
            f"{subset['retry_count'].mean():.1f}",
        )

    console.print(table)

    # Anomalies
    console.print(
        f"\n[bold yellow]Anomalies detected:[/] {result.anomaly_count} "
        f"(threshold score: {result.anomaly_threshold:.3f})"
    )

    anomalies = result.data[result.data["is_anomaly"]].head(10)
    if not anomalies.empty:
        anomaly_table = Table(title="Top Anomalous Workflows")
        anomaly_table.add_column("Workflow ID")
        anomaly_table.add_column("Cluster", justify="right")
        anomaly_table.add_column("Anomaly Score", justify="right")
        anomaly_table.add_column("Steps", justify="right")
        anomaly_table.add_column("Duration", justify="right")

        for _, row in anomalies.iterrows():
            anomaly_table.add_row(
                str(row["workflow_id"]),
                str(row["cluster"]),
                f"{row['anomaly_score']:.3f}",
                str(int(row["step_count"])),
                f"{row['duration_seconds']:.1f}",
            )
        console.print(anomaly_table)

    # Trend
    if result.trend_summary is not None:
        console.print("\n[bold green]Weekly Cluster Trend (last 5 weeks):[/]")
        console.print(result.trend_summary.tail(5).to_string())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Workflow pattern detection experiment")
    parser.add_argument("--samples", type=int, default=500, help="Number of synthetic samples")
    parser.add_argument("--clusters", type=int, default=3, help="Number of clusters")
    parser.add_argument("--anomaly-percentile", type=float, default=95.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    console.print("[bold]Generating synthetic workflow data...[/]")
    df = generate_synthetic_workflows(n_samples=args.samples, seed=args.seed)

    console.print(f"[bold]Running pattern detection (k={args.clusters})...[/]")
    result = detect_patterns(
        df, n_clusters=args.clusters, anomaly_percentile=args.anomaly_percentile
    )

    print_report(result)
    console.print("\n[bold green]Experiment complete.[/]")


if __name__ == "__main__":
    main()
