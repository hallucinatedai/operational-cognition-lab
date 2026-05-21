# Evaluation Framework

## Overview

A base framework for running, measuring, and comparing experiments in the
Operational Cognition Lab. Provides:

- **Experiment** base class with lifecycle hooks (setup → run → teardown)
- **MetricCollector** for recording and aggregating metrics
- **ExperimentRunner** for executing experiments with consistent reporting

## Usage

```python
from evaluations.evaluation_framework import Experiment, Metric, MetricCollector

class MyExperiment(Experiment):
    name = "my-experiment"
    description = "Testing a hypothesis"

    def setup(self):
        self.data = load_data()

    def run(self, collector: MetricCollector):
        result = process(self.data)
        collector.record("accuracy", result.accuracy)
        collector.record("latency_ms", result.latency)

    def teardown(self):
        cleanup()
```

## Running the Demo

```bash
python -m evaluations.evaluation_framework
```

## Contributors

- Akash Raj
- Prem Kumar
