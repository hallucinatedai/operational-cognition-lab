# Operational Cognition Lab

Research and experimentation on AI-native operational intelligence, workflow cognition, organizational memory, and autonomous enterprise systems.

## Vision

Modern enterprises suffer from:
- fragmented operational context
- disconnected workflows
- decision loss
- organizational memory gaps
- cognitive overload
- operational friction

Operational Cognition Lab explores how AI systems can augment and eventually transform enterprise operational intelligence.

## Research Themes

### Operational Cognition
Designing systems that understand workflows, operational states, organizational context, human decisions, and execution patterns.

### Organizational Memory
Persistent enterprise memory systems capable of retaining decisions, preserving reasoning, tracking historical context, and supporting long-term intelligence.

### Workflow Intelligence
AI-native orchestration systems that route work dynamically, understand dependencies, optimise execution, and reduce operational friction.

### Decision Intelligence
Tools for replaying, analysing, and improving enterprise decision-making through structured decision records and bias detection.

### Human-AI Collaboration
Exploring how humans and AI systems collaborate in operational governance, enterprise workflows, strategic decisions, and execution management.

## Repository Structure

```
operational-cognition-lab/
├── experiments/
│   ├── workflow_cognition/          # Workflow pattern detection via clustering
│   ├── organizational_memory/       # Memory persistence strategy comparison
│   └── decision_intelligence/       # Decision replay and bias analysis
├── prototypes/
│   ├── conversational_workflow/     # CLI workflow execution via natural language
│   └── autonomous_escalation/       # Rule + heuristic escalation detection
├── evaluations/                     # Base evaluation framework
├── whitepapers/                     # Vision documents
├── docs/                            # Research themes and documentation
├── tests/                           # Test suite
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+

### Installation

```bash
# Clone the repository
git clone https://github.com/hallucinatedai/operational-cognition-lab.git
cd operational-cognition-lab

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Running Experiments

```bash
# Workflow pattern detection
python -m experiments.workflow_cognition.workflow_pattern_detection

# Memory persistence evaluation
python -m experiments.organizational_memory.memory_persistence_eval

# Decision replay analysis
python -m experiments.decision_intelligence.decision_replay
```

### Running Prototypes

```bash
# Conversational workflow (interactive)
python -m prototypes.conversational_workflow.prototype

# Conversational workflow (demo mode)
python -m prototypes.conversational_workflow.prototype --demo

# Autonomous escalation (demo mode)
python -m prototypes.autonomous_escalation.prototype --demo

# Autonomous escalation (interactive)
python -m prototypes.autonomous_escalation.prototype
```

### Running the Evaluation Framework

```bash
python -m evaluations.evaluation_framework
```

### Running Tests

```bash
pytest
```

## Research Questions

- What does enterprise software look like after conversational AI?
- How should operational memory systems evolve?
- Can workflows become autonomous?
- How do organizations preserve decision intelligence?
- What replaces traditional operational dashboards?
- How should provenance and trust work in enterprise AI?

## Long-Term Goal

Build foundational thinking and prototypes for:
- AI-native enterprises
- autonomous operational systems
- organizational cognition infrastructure
- enterprise memory systems
- workflow intelligence platforms

## Documentation

- [Research Themes](docs/research_themes.md) — Structured overview of all research directions
- [AI-Native Enterprise Vision](whitepapers/ai_native_enterprise_vision.md) — Vision whitepaper

## Contributors

- Akash Raj
- Prem Kumar

## License

MIT
