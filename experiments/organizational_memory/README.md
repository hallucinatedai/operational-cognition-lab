# Memory Persistence Evaluation

## Overview

This experiment evaluates different strategies for persisting organizational
memory — the collective decisions, context, and reasoning that accumulate
during enterprise operations.

## Strategies Compared

| Strategy | Description |
|----------|-------------|
| **Flat log** | Append-only log of events; search by scanning |
| **Indexed store** | Key-value store with inverted index for fast retrieval |
| **Hierarchical** | Tree-structured memory with summarisation at each level |
| **Embedding-based** | Dense vector store with semantic similarity retrieval |

## Metrics

- **Write latency** — Time to persist a new memory entry
- **Read latency** — Time to retrieve relevant memories given a query
- **Recall@k** — Fraction of relevant memories retrieved in top-k results
- **Storage efficiency** — Bytes per memory entry
- **Staleness resistance** — Retrieval quality as the store grows

## Running

```bash
python -m experiments.organizational_memory.memory_persistence_eval
```

## Output

Comparison tables and summary statistics for each strategy across all metrics.

## Contributors

- Akash Raj
- Prem Kumar
