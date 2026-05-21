# Workflow Pattern Detection

## Overview

This experiment detects recurring patterns in workflow execution data using
unsupervised machine learning. It identifies clusters of similar workflow
executions, surfaces anomalous runs, and provides insight into how workflows
evolve over time.

## Approach

1. **Feature extraction** — Convert raw workflow execution traces into
   numerical feature vectors (step counts, durations, failure rates, etc.).
2. **Clustering** — Apply K-Means to group similar executions.
3. **Anomaly scoring** — Flag executions that are far from any cluster centroid.
4. **Trend analysis** — Track cluster membership over time to detect drift.

## Running

```bash
python -m experiments.workflow_cognition.workflow_pattern_detection
```

## Input Format

The experiment generates synthetic workflow data by default. To use your own
data, provide a CSV with columns:

| Column | Type | Description |
|--------|------|-------------|
| `workflow_id` | str | Unique workflow identifier |
| `step_count` | int | Number of steps in the execution |
| `duration_seconds` | float | Total execution time |
| `failure_rate` | float | Fraction of steps that failed (0-1) |
| `retry_count` | int | Number of retries during execution |
| `timestamp` | datetime | When the execution started |

## Output

- Cluster assignments for each workflow execution
- Anomaly scores with flagged outliers
- Summary statistics per cluster
- Trend report showing cluster evolution

## Contributors

- Akash Raj
- Prem Kumar
