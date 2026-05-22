"""Conversational workflow prototype — execute enterprise workflows via natural language.

Maps user text to predefined workflows using keyword-based intent parsing and
executes each workflow step with simulated side-effects and rich terminal output.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    name: str
    description: str
    duration_seconds: float = 0.3
    status: StepStatus = StepStatus.PENDING
    output: str = ""


@dataclass
class Workflow:
    name: str
    intent_keywords: list[str]
    steps: list[WorkflowStep] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Workflow definitions
# ---------------------------------------------------------------------------

def _deployment_workflow() -> Workflow:
    return Workflow(
        name="Deployment",
        intent_keywords=["deploy", "release", "ship"],
        steps=[
            WorkflowStep("validate", "Validating deployment configuration"),
            WorkflowStep("build", "Building artifacts"),
            WorkflowStep("test", "Running pre-deployment tests"),
            WorkflowStep("deploy", "Deploying to target environment"),
            WorkflowStep("notify", "Sending deployment notification"),
        ],
    )


def _incident_workflow() -> Workflow:
    return Workflow(
        name="Incident Response",
        intent_keywords=["incident", "outage", "alert", "page"],
        steps=[
            WorkflowStep("triage", "Assessing severity and impact"),
            WorkflowStep("investigate", "Gathering logs and metrics"),
            WorkflowStep("mitigate", "Applying mitigation steps"),
            WorkflowStep("review", "Conducting post-incident review"),
        ],
    )


def _review_workflow() -> Workflow:
    return Workflow(
        name="Code Review",
        intent_keywords=["review", "pr", "pull request", "merge"],
        steps=[
            WorkflowStep("fetch", "Fetching code changes"),
            WorkflowStep("analyse", "Running static analysis"),
            WorkflowStep("comment", "Generating review comments"),
            WorkflowStep("summarise", "Creating review summary"),
        ],
    )


def _onboarding_workflow() -> Workflow:
    return Workflow(
        name="Onboarding",
        intent_keywords=["onboard", "new member", "new hire", "welcome"],
        steps=[
            WorkflowStep("provision", "Provisioning accounts and access"),
            WorkflowStep("configure", "Setting up development environment"),
            WorkflowStep("verify", "Verifying access and permissions"),
            WorkflowStep("welcome", "Sending welcome package"),
        ],
    )


WORKFLOW_REGISTRY: list[Workflow] = [
    _deployment_workflow(),
    _incident_workflow(),
    _review_workflow(),
    _onboarding_workflow(),
]


# ---------------------------------------------------------------------------
# Intent parsing
# ---------------------------------------------------------------------------

def parse_intent(user_input: str) -> Workflow | None:
    """Match user text to a workflow by keyword overlap."""
    text = user_input.lower().strip()
    best_match: Workflow | None = None
    best_score = 0

    for workflow_template in WORKFLOW_REGISTRY:
        score = sum(1 for kw in workflow_template.intent_keywords if kw in text)
        if score > best_score:
            best_score = score
            best_match = workflow_template

    if best_match is None or best_score == 0:
        return None

    # Return a fresh copy so steps are independent
    return Workflow(
        name=best_match.name,
        intent_keywords=best_match.intent_keywords,
        steps=[
            WorkflowStep(s.name, s.description, s.duration_seconds)
            for s in best_match.steps
        ],
    )


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def execute_workflow(workflow: Workflow) -> bool:
    """Execute workflow steps sequentially with progress display."""
    console.print(
        Panel(
            f"[bold cyan]{workflow.name}[/bold cyan]\n"
            f"Steps: {', '.join(s.name for s in workflow.steps)}",
            title="Workflow Started",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for step in workflow.steps:
            task = progress.add_task(f"{step.name}: {step.description}", total=1)
            step.status = StepStatus.RUNNING
            time.sleep(step.duration_seconds)
            step.status = StepStatus.COMPLETED
            step.output = f"{step.name} completed successfully"
            progress.update(task, completed=1)

    # Summary
    completed = sum(1 for s in workflow.steps if s.status == StepStatus.COMPLETED)
    total = len(workflow.steps)
    console.print(
        f"\n[bold green]Workflow '{workflow.name}' finished: "
        f"{completed}/{total} steps completed.[/bold green]\n"
    )
    return completed == total


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

def interactive_loop() -> None:
    """Run the conversational workflow REPL."""
    console.print(
        Panel(
            "[bold]Conversational Workflow Engine[/bold]\n\n"
            "Describe what you need and I'll find the right workflow.\n"
            "Examples:\n"
            "  • deploy the payment service\n"
            "  • start incident response for database outage\n"
            "  • review PR 42\n"
            "  • onboard new team member\n\n"
            "Type [bold yellow]quit[/bold yellow] or [bold yellow]exit[/bold yellow] to leave.",
            title="Welcome",
        )
    )

    while True:
        try:
            user_input = console.input("[bold cyan]>>> [/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break

        text = user_input.strip()
        if not text:
            continue
        if text.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        workflow = parse_intent(text)
        if workflow is None:
            console.print(
                "[yellow]Could not identify a workflow from your input. "
                "Try keywords like: deploy, incident, review, onboard.[/yellow]\n"
            )
            continue

        execute_workflow(workflow)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Conversational workflow prototype")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a non-interactive demo instead of the REPL",
    )
    args = parser.parse_args(argv)

    if args.demo:
        demo_inputs = [
            "deploy the payment service to production",
            "there is a database outage, start incident response",
            "review the latest pull request",
            "onboard a new engineer to the platform team",
        ]
        for demo_input in demo_inputs:
            console.print(f"\n[bold cyan]>>> {demo_input}[/bold cyan]")
            workflow = parse_intent(demo_input)
            if workflow:
                execute_workflow(workflow)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
