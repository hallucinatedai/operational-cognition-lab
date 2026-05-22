# Conversational Workflow Prototype

## Overview

A CLI-based prototype that lets users execute enterprise workflows through
natural-language-style commands. Instead of navigating complex UIs or writing
YAML, users describe what they want in plain text and the system maps it to a
predefined workflow graph.

## Architecture

```
User Input (text) ──> Intent Parser ──> Workflow Router ──> Step Executor ──> Output
```

1. **Intent Parser** — Keyword + pattern matching to classify user intent.
2. **Workflow Router** — Maps intents to registered workflow definitions.
3. **Step Executor** — Runs workflow steps sequentially, collecting results.
4. **Output Renderer** — Rich terminal output for each step.

## Supported Workflows

| Intent keyword | Workflow | Steps |
|----------------|----------|-------|
| `deploy` | Deployment | validate → build → test → deploy → notify |
| `incident` | Incident response | triage → investigate → mitigate → review |
| `review` | Code review | fetch → analyse → comment → summarise |
| `onboard` | Onboarding | provision → configure → verify → welcome |

## Running

```bash
python -m prototypes.conversational_workflow.prototype
```

Then type commands like:
- `deploy the payment service`
- `start incident response for database outage`
- `review PR 42`
- `onboard new team member`

Type `quit` or `exit` to leave.

## Contributors

- Akash Raj
- Prem Kumar
