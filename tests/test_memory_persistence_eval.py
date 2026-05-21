"""Tests for memory persistence evaluation experiment."""

from experiments.organizational_memory.memory_persistence_eval import (
    EmbeddingStore,
    FlatLogStore,
    HierarchicalStore,
    IndexedStore,
    MemoryEntry,
    generate_entries,
)


def _make_entry(entry_id: str = "test-001", tags: tuple[str, ...] = ("a", "b")) -> MemoryEntry:
    return MemoryEntry(
        entry_id=entry_id,
        content="Test memory content",
        tags=tags,
        timestamp=1000.0,
        importance=0.8,
    )


def test_flat_log_write_and_query():
    store = FlatLogStore()
    store.write(_make_entry("e1", ("deploy", "security")))
    store.write(_make_entry("e2", ("deploy",)))
    results = store.query(("deploy",), top_k=2)
    assert len(results) == 2


def test_indexed_store_retrieves_by_tag():
    store = IndexedStore()
    store.write(_make_entry("e1", ("deploy",)))
    store.write(_make_entry("e2", ("incident",)))
    results = store.query(("deploy",), top_k=5)
    assert len(results) == 1
    assert results[0].entry_id == "e1"


def test_hierarchical_store_buckets():
    store = HierarchicalStore()
    store.write(_make_entry("e1", ("deploy", "security")))
    store.write(_make_entry("e2", ("incident",)))
    results = store.query(("deploy",), top_k=5)
    assert len(results) == 1


def test_embedding_store_returns_results():
    store = EmbeddingStore(dim=16, seed=0)
    for i in range(10):
        store.write(_make_entry(f"e{i}", ("deploy", "security")))
    results = store.query(("deploy",), top_k=3)
    assert len(results) == 3


def test_generate_entries_deterministic():
    e1 = generate_entries(n=20, seed=5)
    e2 = generate_entries(n=20, seed=5)
    assert [e.entry_id for e in e1] == [e.entry_id for e in e2]


def test_all_stores_report_size():
    stores = [FlatLogStore(), IndexedStore(), HierarchicalStore(), EmbeddingStore()]
    entry = _make_entry()
    for store in stores:
        store.write(entry)
        assert store.size_bytes() > 0
