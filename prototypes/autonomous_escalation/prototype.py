"""Autonomous escalation detection prototype.

Combines rule-based checks with heuristic scoring to determine whether an
operational event requires escalation, what level, and to whom.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum, IntEnum

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


class EscalationLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


RESPONDER_MAP: dict[EscalationLevel, str] = {
    EscalationLevel.NONE: "No action needed",
    EscalationLevel.LOW: "On-call engineer",
    EscalationLevel.MEDIUM: "Engineering lead",
    EscalationLevel.HIGH: "VP Engineering",
    EscalationLevel.CRITICAL: "CTO / Incident commander",
}


@dataclass(frozen=True)
class OperationalEvent:
    event_id: str
    title: str
    severity: Severity
    impact_users: int
    duration_minutes: float
    services_affected: int
    is_recurring: bool
    is_customer_facing: bool


@dataclass
class EscalationDecision:
    event: OperationalEvent
    rule_triggered: str | None
    heuristic_score: float
    level: EscalationLevel
    responder: str
    rationale: list[str]


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def apply_rules(event: OperationalEvent) -> tuple[str | None, list[str]]:
    """Hard-coded rules for immediate escalation triggers."""
    rationale: list[str] = []

    if event.severity == Severity.CRITICAL:
        rationale.append("Severity is CRITICAL — immediate escalation required")
        return "critical_severity", rationale

    if event.impact_users >= 10000:
        rationale.append(f"Impact affects {event.impact_users:,} users — mass impact rule")
        return "mass_impact", rationale

    if event.duration_minutes >= 120 and event.is_customer_facing:
        rationale.append(
            f"Customer-facing issue for {event.duration_minutes:.0f} min — extended outage rule"
        )
        return "extended_outage", rationale

    return None, rationale


# ---------------------------------------------------------------------------
# Heuristic scoring
# ---------------------------------------------------------------------------

WEIGHTS = {
    "severity": 2.5,
    "impact": 2.0,
    "duration": 1.5,
    "services": 1.0,
    "recurring": 1.0,
    "customer_facing": 1.5,
}


def compute_heuristic_score(event: OperationalEvent) -> tuple[float, list[str]]:
    """Weighted heuristic score (0-10 scale)."""
    rationale: list[str] = []

    severity_score = event.severity.value / Severity.CRITICAL.value
    impact_score = min(event.impact_users / 10000, 1.0)
    duration_score = min(event.duration_minutes / 120, 1.0)
    services_score = min(event.services_affected / 10, 1.0)
    recurring_score = 1.0 if event.is_recurring else 0.0
    customer_facing_score = 1.0 if event.is_customer_facing else 0.0

    components = {
        "severity": severity_score * WEIGHTS["severity"],
        "impact": impact_score * WEIGHTS["impact"],
        "duration": duration_score * WEIGHTS["duration"],
        "services": services_score * WEIGHTS["services"],
        "recurring": recurring_score * WEIGHTS["recurring"],
        "customer_facing": customer_facing_score * WEIGHTS["customer_facing"],
    }

    total_weight = sum(WEIGHTS.values())
    raw_score = sum(components.values()) / total_weight * 10

    for name, value in components.items():
        if value > 0:
            rationale.append(f"{name}: {value:.2f} (weight {WEIGHTS[name]})")

    return round(raw_score, 2), rationale


def score_to_level(score: float) -> EscalationLevel:
    if score >= 9:
        return EscalationLevel.CRITICAL
    if score >= 7:
        return EscalationLevel.HIGH
    if score >= 5:
        return EscalationLevel.MEDIUM
    if score >= 3:
        return EscalationLevel.LOW
    return EscalationLevel.NONE


# ---------------------------------------------------------------------------
# Decision pipeline
# ---------------------------------------------------------------------------

def evaluate_event(event: OperationalEvent) -> EscalationDecision:
    """Run the full escalation evaluation pipeline for one event."""
    rule_name, rule_rationale = apply_rules(event)
    heuristic_score, heuristic_rationale = compute_heuristic_score(event)

    # Rules override heuristic when triggered
    if rule_name is not None:
        level = EscalationLevel.CRITICAL
    else:
        level = score_to_level(heuristic_score)

    return EscalationDecision(
        event=event,
        rule_triggered=rule_name,
        heuristic_score=heuristic_score,
        level=level,
        responder=RESPONDER_MAP[level],
        rationale=rule_rationale + heuristic_rationale,
    )


# ---------------------------------------------------------------------------
# Synthetic events
# ---------------------------------------------------------------------------

def generate_sample_events(n: int = 20, seed: int = 42) -> list[OperationalEvent]:
    rng = np.random.default_rng(seed)
    events: list[OperationalEvent] = []

    titles = [
        "API latency spike", "Database connection pool exhaustion",
        "Payment processing failure", "CDN cache invalidation storm",
        "Auth service timeout", "Disk space critical on worker nodes",
        "Memory leak in order service", "Certificate expiration warning",
        "Rate limiter misconfiguration", "DNS resolution failures",
        "Search index corruption", "Message queue backlog growing",
        "Deployment rollback triggered", "Health check flapping",
        "Upstream provider degradation", "Data pipeline stall",
        "Login page 500 errors", "Webhook delivery failures",
        "Cron job timeout", "Network partition detected",
    ]

    for i in range(n):
        events.append(
            OperationalEvent(
                event_id=f"evt-{i:04d}",
                title=titles[i % len(titles)],
                severity=Severity(int(rng.integers(0, 4))),
                impact_users=int(rng.choice([10, 100, 500, 1000, 5000, 10000, 50000])),
                duration_minutes=float(rng.choice([5, 15, 30, 60, 90, 120, 240])),
                services_affected=int(rng.integers(1, 12)),
                is_recurring=bool(rng.random() > 0.7),
                is_customer_facing=bool(rng.random() > 0.4),
            )
        )
    return events


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_decisions(decisions: list[EscalationDecision]) -> None:
    console.rule("[bold blue]Autonomous Escalation Report")

    table = Table(title="Escalation Decisions")
    table.add_column("Event ID", style="dim")
    table.add_column("Title")
    table.add_column("Severity")
    table.add_column("Score", justify="right")
    table.add_column("Level", style="bold")
    table.add_column("Responder")
    table.add_column("Rule")

    level_styles = {
        EscalationLevel.NONE: "dim",
        EscalationLevel.LOW: "green",
        EscalationLevel.MEDIUM: "yellow",
        EscalationLevel.HIGH: "red",
        EscalationLevel.CRITICAL: "bold red",
    }

    for d in decisions:
        table.add_row(
            d.event.event_id,
            d.event.title,
            d.event.severity.name,
            f"{d.heuristic_score:.1f}",
            d.level.value,
            d.responder,
            d.rule_triggered or "-",
            style=level_styles.get(d.level, ""),
        )
    console.print(table)

    # Summary
    level_counts = {}
    for d in decisions:
        level_counts[d.level.value] = level_counts.get(d.level.value, 0) + 1

    console.print("\n[bold]Escalation Distribution:[/]")
    for level_name, count in sorted(level_counts.items()):
        console.print(f"  {level_name}: {count}")


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive_mode() -> None:
    """Evaluate a user-described event interactively."""
    console.print(
        Panel(
            "[bold]Autonomous Escalation Engine[/bold]\n\n"
            "Enter event details to get an escalation recommendation.\n"
            "Type [bold yellow]quit[/bold yellow] to exit.",
            title="Escalation Prototype",
        )
    )

    event_counter = 0
    while True:
        try:
            title = console.input("\n[cyan]Event title (or quit): [/cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if title.lower() in ("quit", "exit", "q") or not title:
            break

        try:
            sev_input = console.input(
                "[cyan]Severity (0=info, 1=warning, 2=error, 3=critical): [/cyan]"
            )
            severity = Severity(int(sev_input.strip()))
            impact = int(console.input("[cyan]Users impacted: [/cyan]").strip())
            duration = float(console.input("[cyan]Duration (minutes): [/cyan]").strip())
            services = int(console.input("[cyan]Services affected: [/cyan]").strip())
            recurring = console.input("[cyan]Recurring? (y/n): [/cyan]").strip().lower() == "y"
            cf_input = console.input("[cyan]Customer-facing? (y/n): [/cyan]")
            customer_facing = cf_input.strip().lower() == "y"
        except (ValueError, EOFError, KeyboardInterrupt):
            console.print("[red]Invalid input, skipping.[/red]")
            continue

        event = OperationalEvent(
            event_id=f"interactive-{event_counter:03d}",
            title=title,
            severity=severity,
            impact_users=impact,
            duration_minutes=duration,
            services_affected=services,
            is_recurring=recurring,
            is_customer_facing=customer_facing,
        )
        event_counter += 1

        decision = evaluate_event(event)
        print_decisions([decision])

        console.print("\n[bold]Rationale:[/bold]")
        for line in decision.rationale:
            console.print(f"  • {line}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Autonomous escalation prototype")
    parser.add_argument("--demo", action="store_true", help="Run non-interactive demo")
    parser.add_argument("--events", type=int, default=20, help="Number of demo events")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    if args.demo:
        events = generate_sample_events(n=args.events, seed=args.seed)
        decisions = [evaluate_event(e) for e in events]
        print_decisions(decisions)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
