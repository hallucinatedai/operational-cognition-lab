# Autonomous Escalation Detection Prototype

## Overview

A prototype that automatically detects when an operational situation requires
escalation — combining rule-based checks with heuristic scoring to decide
whether to escalate, to whom, and with what urgency.

## Architecture

```
Event Stream ──> Rule Engine ──> Heuristic Scorer ──> Escalation Router ──> Action
```

1. **Rule Engine** — Hard-coded rules for critical conditions (e.g. severity ≥ critical).
2. **Heuristic Scorer** — Weighted scoring based on impact, duration, blast radius, etc.
3. **Escalation Router** — Maps escalation level to the appropriate responder tier.
4. **Action** — Outputs the escalation decision with rationale.

## Escalation Levels

| Level | Trigger | Responder |
|-------|---------|-----------|
| **None** | Score < 3 | No escalation needed |
| **Low** | 3 ≤ Score < 5 | On-call engineer |
| **Medium** | 5 ≤ Score < 7 | Engineering lead |
| **High** | 7 ≤ Score < 9 | VP Engineering |
| **Critical** | Score ≥ 9 | CTO / Incident commander |

## Running

```bash
python -m prototypes.autonomous_escalation.prototype
```

Use `--demo` for a non-interactive demonstration with sample events.

## Contributors

- Akash Raj
- Prem Kumar
