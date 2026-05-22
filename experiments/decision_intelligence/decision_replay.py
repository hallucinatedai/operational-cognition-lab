"""Replay and analyse historical decisions to surface patterns and biases.

Generates synthetic decision logs, computes quality metrics, evaluates
calibration (confidence vs. outcome), and detects common cognitive biases.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

DECISION_MAKERS = ["engineering", "product", "security", "operations", "leadership"]

BIAS_LABELS = [
    "status_quo",
    "recency",
    "anchoring",
    "confirmation",
    "sunk_cost",
]


def generate_decision_log(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Create a synthetic log of enterprise decisions."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    base_time = datetime(2024, 6, 1)

    for i in range(n):
        confidence = float(rng.uniform(0.3, 1.0))
        time_pressure = float(rng.uniform(0.0, 1.0))

        # Outcome is loosely correlated with confidence but degraded by time pressure
        noise = rng.normal(0, 0.15)
        outcome = np.clip(confidence * 0.6 + (1 - time_pressure) * 0.3 + noise, 0, 1)

        options_considered = int(rng.integers(2, 7))
        rows.append(
            {
                "decision_id": f"dec-{i:04d}",
                "decision_maker": rng.choice(DECISION_MAKERS),
                "options_considered": options_considered,
                "chosen_option": int(rng.integers(0, options_considered)),
                "confidence": round(confidence, 3),
                "outcome_score": round(float(outcome), 3),
                "time_pressure": round(time_pressure, 3),
                "timestamp": base_time + timedelta(days=int(rng.integers(0, 365))),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

@dataclass
class CalibrationBucket:
    confidence_range: str
    n_decisions: int
    avg_confidence: float
    avg_outcome: float
    calibration_gap: float


@dataclass
class BiasIndicator:
    bias_name: str
    signal_strength: float  # 0-1
    description: str


@dataclass
class ReplayResult:
    data: pd.DataFrame
    quality_stats: dict[str, float]
    calibration: list[CalibrationBucket]
    biases: list[BiasIndicator]
    maker_stats: pd.DataFrame


def analyse_calibration(df: pd.DataFrame, n_buckets: int = 5) -> list[CalibrationBucket]:
    """Bin decisions by confidence and compare to actual outcomes."""
    df = df.copy()
    df["conf_bucket"] = pd.cut(df["confidence"], bins=n_buckets)
    buckets: list[CalibrationBucket] = []
    for interval, group in df.groupby("conf_bucket", observed=True):
        avg_conf = group["confidence"].mean()
        avg_out = group["outcome_score"].mean()
        buckets.append(
            CalibrationBucket(
                confidence_range=str(interval),
                n_decisions=len(group),
                avg_confidence=round(avg_conf, 3),
                avg_outcome=round(avg_out, 3),
                calibration_gap=round(avg_conf - avg_out, 3),
            )
        )
    return buckets


def detect_biases(df: pd.DataFrame) -> list[BiasIndicator]:
    """Heuristic bias detection based on decision patterns."""
    indicators: list[BiasIndicator] = []

    # Status-quo bias: chosen_option == 0 disproportionately
    first_option_rate = (df["chosen_option"] == 0).mean()
    expected_rate = 1 / df["options_considered"].mean()
    sq_signal = max(0, (first_option_rate - expected_rate) / max(expected_rate, 0.01))
    indicators.append(
        BiasIndicator(
            bias_name="Status Quo",
            signal_strength=round(min(float(sq_signal), 1.0), 3),
            description="First/default option chosen more often than expected",
        )
    )

    # Recency bias: recent decisions have higher confidence regardless of outcome
    df_sorted = df.sort_values("timestamp")
    n = len(df_sorted)
    recent_conf = df_sorted.tail(n // 4)["confidence"].mean()
    older_conf = df_sorted.head(n // 4)["confidence"].mean()
    recency_signal = max(0, (recent_conf - older_conf) / max(older_conf, 0.01))
    indicators.append(
        BiasIndicator(
            bias_name="Recency",
            signal_strength=round(min(float(recency_signal), 1.0), 3),
            description="Recent decisions show inflated confidence",
        )
    )

    # Time-pressure degradation: high time pressure correlates with worse outcomes
    high_pressure = df[df["time_pressure"] > 0.7]
    low_pressure = df[df["time_pressure"] < 0.3]
    if len(high_pressure) > 0 and len(low_pressure) > 0:
        gap = low_pressure["outcome_score"].mean() - high_pressure["outcome_score"].mean()
        indicators.append(
            BiasIndicator(
                bias_name="Time Pressure",
                signal_strength=round(min(max(float(gap), 0), 1.0), 3),
                description="Rushed decisions yield measurably worse outcomes",
            )
        )

    # Overconfidence: average confidence exceeds average outcome
    overconf = df["confidence"].mean() - df["outcome_score"].mean()
    indicators.append(
        BiasIndicator(
            bias_name="Overconfidence",
            signal_strength=round(min(max(float(overconf), 0), 1.0), 3),
            description="Stated confidence systematically exceeds actual outcomes",
        )
    )

    return indicators


def replay_decisions(df: pd.DataFrame) -> ReplayResult:
    """Run the full decision replay analysis."""
    quality_stats = {
        "mean_outcome": round(float(df["outcome_score"].mean()), 3),
        "std_outcome": round(float(df["outcome_score"].std()), 3),
        "median_outcome": round(float(df["outcome_score"].median()), 3),
        "poor_decisions_pct": round(float((df["outcome_score"] < 0.4).mean()) * 100, 1),
    }

    calibration = analyse_calibration(df)
    biases = detect_biases(df)

    maker_stats = (
        df.groupby("decision_maker")
        .agg(
            count=("decision_id", "count"),
            avg_outcome=("outcome_score", "mean"),
            avg_confidence=("confidence", "mean"),
            avg_options=("options_considered", "mean"),
        )
        .round(3)
    )

    return ReplayResult(
        data=df,
        quality_stats=quality_stats,
        calibration=calibration,
        biases=biases,
        maker_stats=maker_stats,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(result: ReplayResult) -> None:
    console.rule("[bold blue]Decision Replay Analysis")

    # Quality overview
    console.print("\n[bold]Decision Quality Summary[/]")
    for key, value in result.quality_stats.items():
        console.print(f"  {key}: {value}")

    # Calibration
    cal_table = Table(title="\nCalibration Analysis")
    cal_table.add_column("Confidence Range")
    cal_table.add_column("Count", justify="right")
    cal_table.add_column("Avg Confidence", justify="right")
    cal_table.add_column("Avg Outcome", justify="right")
    cal_table.add_column("Gap", justify="right")

    for bucket in result.calibration:
        style = "red" if bucket.calibration_gap > 0.1 else ""
        cal_table.add_row(
            bucket.confidence_range,
            str(bucket.n_decisions),
            f"{bucket.avg_confidence:.3f}",
            f"{bucket.avg_outcome:.3f}",
            f"{bucket.calibration_gap:+.3f}",
            style=style,
        )
    console.print(cal_table)

    # Biases
    bias_table = Table(title="Bias Indicators")
    bias_table.add_column("Bias", style="cyan")
    bias_table.add_column("Signal", justify="right")
    bias_table.add_column("Description")

    for bias in result.biases:
        style = "red bold" if bias.signal_strength > 0.3 else ""
        bias_table.add_row(
            bias.bias_name,
            f"{bias.signal_strength:.3f}",
            bias.description,
            style=style,
        )
    console.print(bias_table)

    # Per-maker stats
    console.print("\n[bold]Decision Maker Statistics[/]")
    console.print(result.maker_stats.to_string())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Decision replay experiment")
    parser.add_argument("--decisions", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    console.print("[bold]Generating decision log...[/]")
    df = generate_decision_log(n=args.decisions, seed=args.seed)

    console.print("[bold]Replaying decisions...[/]")
    result = replay_decisions(df)

    print_report(result)
    console.print("\n[bold green]Replay complete.[/]")


if __name__ == "__main__":
    main()
