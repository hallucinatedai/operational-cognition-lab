"""Tests for prototypes."""

from prototypes.autonomous_escalation.prototype import (
    EscalationLevel,
    OperationalEvent,
    Severity,
    evaluate_event,
    generate_sample_events,
    score_to_level,
)
from prototypes.conversational_workflow.prototype import (
    parse_intent,
)

# -- Conversational workflow --------------------------------------------------


def test_parse_intent_deploy():
    wf = parse_intent("deploy the payment service")
    assert wf is not None
    assert wf.name == "Deployment"


def test_parse_intent_incident():
    wf = parse_intent("start incident response")
    assert wf is not None
    assert wf.name == "Incident Response"


def test_parse_intent_review():
    wf = parse_intent("review PR 42")
    assert wf is not None
    assert wf.name == "Code Review"


def test_parse_intent_onboard():
    wf = parse_intent("onboard new team member")
    assert wf is not None
    assert wf.name == "Onboarding"


def test_parse_intent_unknown():
    wf = parse_intent("do something random and unrelated")
    assert wf is None


# -- Autonomous escalation ----------------------------------------------------


def test_critical_severity_triggers_rule():
    event = OperationalEvent(
        event_id="test-001",
        title="Critical failure",
        severity=Severity.CRITICAL,
        impact_users=10,
        duration_minutes=1,
        services_affected=1,
        is_recurring=False,
        is_customer_facing=False,
    )
    decision = evaluate_event(event)
    assert decision.level == EscalationLevel.CRITICAL
    assert decision.rule_triggered == "critical_severity"


def test_mass_impact_triggers_rule():
    event = OperationalEvent(
        event_id="test-002",
        title="Mass impact",
        severity=Severity.WARNING,
        impact_users=50000,
        duration_minutes=5,
        services_affected=2,
        is_recurring=False,
        is_customer_facing=True,
    )
    decision = evaluate_event(event)
    assert decision.level == EscalationLevel.CRITICAL
    assert decision.rule_triggered == "mass_impact"


def test_low_severity_no_escalation():
    event = OperationalEvent(
        event_id="test-003",
        title="Minor log warning",
        severity=Severity.INFO,
        impact_users=0,
        duration_minutes=1,
        services_affected=1,
        is_recurring=False,
        is_customer_facing=False,
    )
    decision = evaluate_event(event)
    assert decision.level == EscalationLevel.NONE


def test_score_to_level_boundaries():
    assert score_to_level(0) == EscalationLevel.NONE
    assert score_to_level(3) == EscalationLevel.LOW
    assert score_to_level(5) == EscalationLevel.MEDIUM
    assert score_to_level(7) == EscalationLevel.HIGH
    assert score_to_level(9) == EscalationLevel.CRITICAL


def test_generate_sample_events_deterministic():
    e1 = generate_sample_events(n=10, seed=0)
    e2 = generate_sample_events(n=10, seed=0)
    assert [e.event_id for e in e1] == [e.event_id for e in e2]
