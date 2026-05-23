"""Evaluate different memory persistence strategies for organizational memory.

Compares flat-log, indexed, hierarchical, and embedding-based approaches
across write latency, read latency, recall, and storage efficiency.
"""

from __future__ import annotations

import argparse
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Memory entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryEntry:
    """A single unit of organizational memory."""

    entry_id: str
    content: str
    tags: tuple[str, ...]
    timestamp: float
    importance: float  # 0-1


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class MemoryStore(ABC):
    """Abstract base for a memory persistence strategy."""

    @abstractmethod
    def write(self, entry: MemoryEntry) -> None: ...

    @abstractmethod
    def query(self, query_tags: tuple[str, ...], top_k: int = 5) -> list[MemoryEntry]: ...

    @abstractmethod
    def size_bytes(self) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------


class FlatLogStore(MemoryStore):
    """Append-only log with linear scan retrieval."""

    def __init__(self) -> None:
        self._log: list[MemoryEntry] = []

    @property
    def name(self) -> str:
        return "Flat Log"

    def write(self, entry: MemoryEntry) -> None:
        self._log.append(entry)

    def query(self, query_tags: tuple[str, ...], top_k: int = 5) -> list[MemoryEntry]:
        tag_set = set(query_tags)
        scored = [(sum(1 for t in e.tags if t in tag_set) * e.importance, e) for e in self._log]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def size_bytes(self) -> int:
        return sum(len(e.content.encode()) + len(e.entry_id) + 8 * len(e.tags) for e in self._log)


class IndexedStore(MemoryStore):
    """Key-value store with an inverted index on tags."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._tag_index: dict[str, set[str]] = {}

    @property
    def name(self) -> str:
        return "Indexed Store"

    def write(self, entry: MemoryEntry) -> None:
        self._entries[entry.entry_id] = entry
        for tag in entry.tags:
            self._tag_index.setdefault(tag, set()).add(entry.entry_id)

    def query(self, query_tags: tuple[str, ...], top_k: int = 5) -> list[MemoryEntry]:
        candidate_ids: dict[str, int] = {}
        for tag in query_tags:
            for eid in self._tag_index.get(tag, set()):
                candidate_ids[eid] = candidate_ids.get(eid, 0) + 1

        candidates = [
            (count * self._entries[eid].importance, self._entries[eid])
            for eid, count in candidate_ids.items()
        ]
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in candidates[:top_k]]

    def size_bytes(self) -> int:
        entry_bytes = sum(
            len(e.content.encode()) + len(e.entry_id) + 8 * len(e.tags)
            for e in self._entries.values()
        )
        index_bytes = sum(len(tag) + 8 * len(ids) for tag, ids in self._tag_index.items())
        return entry_bytes + index_bytes


class HierarchicalStore(MemoryStore):
    """Tree-structured store with tag-based hierarchy and summarisation."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[MemoryEntry]] = {}

    @property
    def name(self) -> str:
        return "Hierarchical"

    def write(self, entry: MemoryEntry) -> None:
        primary_tag = entry.tags[0] if entry.tags else "__root__"
        self._buckets.setdefault(primary_tag, []).append(entry)

    def query(self, query_tags: tuple[str, ...], top_k: int = 5) -> list[MemoryEntry]:
        results: list[tuple[float, MemoryEntry]] = []
        tag_set = set(query_tags)
        for tag in query_tags:
            for entry in self._buckets.get(tag, []):
                score = sum(1 for t in entry.tags if t in tag_set) * entry.importance
                results.append((score, entry))

        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:top_k]]

    def size_bytes(self) -> int:
        total = 0
        for tag, entries in self._buckets.items():
            total += len(tag)
            total += sum(
                len(e.content.encode()) + len(e.entry_id) + 8 * len(e.tags) for e in entries
            )
        return total


class EmbeddingStore(MemoryStore):
    """Simulated dense vector store with cosine similarity retrieval."""

    def __init__(self, dim: int = 64, seed: int = 42) -> None:
        self._entries: list[MemoryEntry] = []
        self._vectors: list[np.ndarray] = []
        self._tag_to_vec: dict[str, np.ndarray] = {}
        self._dim = dim
        self._rng = np.random.default_rng(seed)

    @property
    def name(self) -> str:
        return "Embedding-based"

    def _embed(self, tags: tuple[str, ...]) -> np.ndarray:
        vecs = []
        for tag in tags:
            if tag not in self._tag_to_vec:
                self._tag_to_vec[tag] = self._rng.standard_normal(self._dim)
            vecs.append(self._tag_to_vec[tag])
        if not vecs:
            return np.zeros(self._dim)
        combined = np.mean(vecs, axis=0)
        norm = np.linalg.norm(combined)
        return combined / norm if norm > 0 else combined

    def write(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        self._vectors.append(self._embed(entry.tags))

    def query(self, query_tags: tuple[str, ...], top_k: int = 5) -> list[MemoryEntry]:
        query_vec = self._embed(query_tags)
        if not self._vectors:
            return []
        matrix = np.stack(self._vectors)
        similarities = matrix @ query_vec
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [self._entries[i] for i in top_indices]

    def size_bytes(self) -> int:
        entry_bytes = sum(
            len(e.content.encode()) + len(e.entry_id) + 8 * len(e.tags) for e in self._entries
        )
        vector_bytes = len(self._vectors) * self._dim * 8
        return entry_bytes + vector_bytes


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

TAG_POOL = [
    "deployment",
    "incident",
    "review",
    "planning",
    "hiring",
    "security",
    "compliance",
    "architecture",
    "budget",
    "migration",
    "performance",
    "reliability",
    "onboarding",
    "strategy",
    "retrospective",
]


def generate_entries(n: int = 1000, seed: int = 42) -> list[MemoryEntry]:
    rng = np.random.default_rng(seed)
    entries: list[MemoryEntry] = []
    for i in range(n):
        n_tags = rng.integers(1, 5)
        tags = tuple(rng.choice(TAG_POOL, size=n_tags, replace=False).tolist())
        entries.append(
            MemoryEntry(
                entry_id=f"mem-{i:05d}",
                content=f"Organizational memory entry {i} concerning {', '.join(tags)}.",
                tags=tags,
                timestamp=time.time() - rng.integers(0, 86400 * 365),
                importance=float(rng.uniform(0.1, 1.0)),
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@dataclass
class BenchmarkResult:
    strategy_name: str
    avg_write_us: float
    avg_read_us: float
    recall_at_5: float
    storage_bytes: int
    entry_count: int


def evaluate_store(
    store: MemoryStore,
    entries: list[MemoryEntry],
    queries: list[tuple[str, ...]],
    ground_truth: list[set[str]],
) -> BenchmarkResult:
    """Benchmark a single memory store."""
    # Write benchmark
    write_times: list[float] = []
    for entry in entries:
        t0 = time.perf_counter()
        store.write(entry)
        write_times.append(time.perf_counter() - t0)

    # Read benchmark + recall
    read_times: list[float] = []
    recall_scores: list[float] = []
    for qtags, truth in zip(queries, ground_truth):
        t0 = time.perf_counter()
        results = store.query(qtags, top_k=5)
        read_times.append(time.perf_counter() - t0)

        retrieved_ids = {r.entry_id for r in results}
        if truth:
            recall_scores.append(len(retrieved_ids & truth) / min(5, len(truth)))
        else:
            recall_scores.append(1.0)

    return BenchmarkResult(
        strategy_name=store.name,
        avg_write_us=float(np.mean(write_times)) * 1e6,
        avg_read_us=float(np.mean(read_times)) * 1e6,
        recall_at_5=float(np.mean(recall_scores)),
        storage_bytes=store.size_bytes(),
        entry_count=len(entries),
    )


def build_ground_truth(
    entries: list[MemoryEntry],
    queries: list[tuple[str, ...]],
) -> list[set[str]]:
    """Build ground-truth relevant sets by tag overlap * importance scoring."""
    truth: list[set[str]] = []
    for qtags in queries:
        tag_set = set(qtags)
        scored = sorted(
            entries,
            key=lambda e: sum(1 for t in e.tags if t in tag_set) * e.importance,
            reverse=True,
        )
        truth.append({e.entry_id for e in scored[:5]})
    return truth


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_comparison(results: list[BenchmarkResult]) -> None:
    console.rule("[bold blue]Memory Persistence Evaluation")

    table = Table(title="Strategy Comparison")
    table.add_column("Strategy", style="cyan")
    table.add_column("Avg Write (µs)", justify="right")
    table.add_column("Avg Read (µs)", justify="right")
    table.add_column("Recall@5", justify="right")
    table.add_column("Storage (KB)", justify="right")

    for r in results:
        table.add_row(
            r.strategy_name,
            f"{r.avg_write_us:.1f}",
            f"{r.avg_read_us:.1f}",
            f"{r.recall_at_5:.3f}",
            f"{r.storage_bytes / 1024:.1f}",
        )
    console.print(table)

    best_recall = max(results, key=lambda r: r.recall_at_5)
    fastest_read = min(results, key=lambda r: r.avg_read_us)
    smallest = min(results, key=lambda r: r.storage_bytes)

    console.print(f"\n[bold green]Best recall:[/] {best_recall.strategy_name}")
    console.print(f"[bold green]Fastest reads:[/] {fastest_read.strategy_name}")
    console.print(f"[bold green]Most compact:[/] {smallest.strategy_name}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Memory persistence evaluation")
    parser.add_argument("--entries", type=int, default=1000, help="Number of memory entries")
    parser.add_argument("--queries", type=int, default=100, help="Number of test queries")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    console.print("[bold]Generating memory entries...[/]")
    entries = generate_entries(n=args.entries, seed=args.seed)

    rng = np.random.default_rng(args.seed + 1)
    queries: list[tuple[str, ...]] = [
        tuple(rng.choice(TAG_POOL, size=rng.integers(1, 4), replace=False).tolist())
        for _ in range(args.queries)
    ]
    ground_truth = build_ground_truth(entries, queries)

    stores: list[MemoryStore] = [
        FlatLogStore(),
        IndexedStore(),
        HierarchicalStore(),
        EmbeddingStore(seed=args.seed),
    ]

    results: list[BenchmarkResult] = []
    for store in stores:
        console.print(f"[bold]Evaluating {store.name}...[/]")
        results.append(evaluate_store(store, entries, queries, ground_truth))

    print_comparison(results)
    console.print("\n[bold green]Evaluation complete.[/]")


if __name__ == "__main__":
    main()
