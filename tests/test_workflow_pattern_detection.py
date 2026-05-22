"""Tests for workflow pattern detection experiment."""

from experiments.workflow_cognition.workflow_pattern_detection import (
    FEATURE_COLUMNS,
    detect_patterns,
    generate_synthetic_workflows,
)


def test_generate_synthetic_workflows_shape():
    df = generate_synthetic_workflows(n_samples=60, seed=0)
    assert len(df) == 60
    for col in FEATURE_COLUMNS:
        assert col in df.columns


def test_generate_synthetic_workflows_deterministic():
    df1 = generate_synthetic_workflows(n_samples=30, seed=7)
    df2 = generate_synthetic_workflows(n_samples=30, seed=7)
    assert df1.equals(df2)


def test_detect_patterns_assigns_clusters():
    df = generate_synthetic_workflows(n_samples=90, seed=42)
    result = detect_patterns(df, n_clusters=3)
    assert "cluster" in result.data.columns
    assert result.data["cluster"].nunique() == 3


def test_detect_patterns_flags_anomalies():
    df = generate_synthetic_workflows(n_samples=300, seed=42)
    result = detect_patterns(df, n_clusters=3, anomaly_percentile=90.0)
    assert result.anomaly_count > 0
    assert result.data["is_anomaly"].sum() == result.anomaly_count


def test_detect_patterns_cluster_summary():
    df = generate_synthetic_workflows(n_samples=90, seed=42)
    result = detect_patterns(df, n_clusters=3)
    assert not result.cluster_summary.empty
