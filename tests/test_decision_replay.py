"""Tests for decision replay experiment."""

from experiments.decision_intelligence.decision_replay import (
    analyse_calibration,
    detect_biases,
    generate_decision_log,
    replay_decisions,
)


def test_generate_decision_log_shape():
    df = generate_decision_log(n=50, seed=0)
    assert len(df) == 50
    assert "decision_id" in df.columns
    assert "outcome_score" in df.columns


def test_generate_decision_log_deterministic():
    df1 = generate_decision_log(n=30, seed=7)
    df2 = generate_decision_log(n=30, seed=7)
    assert df1.equals(df2)


def test_analyse_calibration_returns_buckets():
    df = generate_decision_log(n=100, seed=42)
    buckets = analyse_calibration(df, n_buckets=5)
    assert len(buckets) > 0
    for b in buckets:
        assert 0 <= b.avg_confidence <= 1
        assert 0 <= b.avg_outcome <= 1


def test_detect_biases_returns_indicators():
    df = generate_decision_log(n=200, seed=42)
    biases = detect_biases(df)
    assert len(biases) >= 3
    for b in biases:
        assert 0 <= b.signal_strength <= 1


def test_replay_decisions_full_pipeline():
    df = generate_decision_log(n=100, seed=42)
    result = replay_decisions(df)
    assert result.quality_stats["mean_outcome"] > 0
    assert not result.maker_stats.empty
