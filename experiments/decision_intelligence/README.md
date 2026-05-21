# Decision Replay

## Overview

This experiment replays and analyses historical decisions to surface patterns,
biases, and improvement opportunities in enterprise decision-making.

Given a log of past decisions (who decided, what options were considered, which
was chosen, what the outcome was), the system:

1. Reconstructs decision context from available data.
2. Computes a quality score based on outcome alignment with stated goals.
3. Identifies decisions that could have gone better with different information.
4. Aggregates statistics to surface systemic biases (e.g. status-quo bias,
   recency bias).

## Running

```bash
python -m experiments.decision_intelligence.decision_replay
```

## Input Format

The experiment generates synthetic decision logs by default. Custom CSV format:

| Column | Type | Description |
|--------|------|-------------|
| `decision_id` | str | Unique identifier |
| `decision_maker` | str | Person or team |
| `options_considered` | int | Number of alternatives evaluated |
| `chosen_option` | int | Index of the chosen option (0-based) |
| `confidence` | float | Stated confidence at decision time (0-1) |
| `outcome_score` | float | Measured outcome quality (0-1) |
| `time_pressure` | float | Perceived urgency (0-1) |
| `timestamp` | datetime | When the decision was made |

## Output

- Decision quality distribution
- Calibration analysis (confidence vs. outcome)
- Bias indicators
- Recommendations for process improvement

## Contributors

- Akash Raj
- Prem Kumar
