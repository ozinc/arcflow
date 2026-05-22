# Deadline-Aware Query — Bounded Wall-Clock Budget for Live UX

> **`MATCH (f:Frame) WHERE f.play_id = 1024 RETURN f LIMIT 100`
> against a Lakehouse partition with a 100-millisecond wall-clock
> budget. The engine returns what it has at the deadline plus a
> `transport_outcome` verdict (`complete` or `truncated`). The
> response is deterministic for a given snapshot — the same query
> at the same deadline against the same snapshot produces the same
> truncated rows.**

**Audience:** python · data-engineer · ml · agent
**Runtime:** ~3 minutes (synthesised sample)
**Pins:** `oz-arcflow==0.8.0`

The cookbook for any system that values **freshness over completeness**:
frame-clock replay (a 30 FPS replay can't wait 200 ms for the engine
to finish), live-broadcast tickers (the score updates by the deadline
or the user sees nothing), partial-consensus aggregations (return the
3-of-4 sources we have, mark the 4th pending), bounded counterfactual
exploration (explore as many branches as fit in 50 ms; report which
were explored).

## What deadline-mode is

ArcFlow's deadline-mode (PAT-0053) is a per-query wall-clock budget:

```python
result = db.execute(
    "MATCH (f:Frame) WHERE f.play_id = 1024 RETURN f LIMIT 100",
    options=arcflow.QueryOptions(deadline_ms=100),
)
result.transport_outcome   # 'truncated' | 'complete' | None
result.io_stats            # IoStats(...)
```

When the deadline fires, the engine:

1. **Lets the current range fetch finish** — no torn reads, no half-bytes.
2. **Skips subsequent ranges** in the read plan.
3. **Returns the partial result** the query had accumulated.
4. **Stamps `transport_outcome = 'truncated'`** so the caller knows the result is incomplete.

If the query finishes within the budget, `transport_outcome = 'complete'` and the result is identical to a deadline-free run.

## What this shows

The recipe synthesises a wide-ish Hive-partitioned Parquet tree
(~50k rows over 5 partitions; one column varies in compression
density to make some reads slower than others). Then it runs the
same query twice:

```python
# Run 1: generous deadline — completes
result_complete = db.execute(
    "MATCH (f:Frame) WHERE f.x > 50.0 RETURN f",
    options=arcflow.QueryOptions(deadline_ms=5000),
)
# result_complete.transport_outcome == 'complete'
# result_complete.io_stats.bytes_read == FULL_PARTITION_BYTES

# Run 2: tight deadline — truncates
result_truncated = db.execute(
    "MATCH (f:Frame) WHERE f.x > 50.0 RETURN f",
    options=arcflow.QueryOptions(deadline_ms=10),
)
# result_truncated.transport_outcome == 'truncated'
# result_truncated.io_stats.bytes_read <  FULL_PARTITION_BYTES
# len(result_truncated.rows) <  len(result_complete.rows)
```

Both runs are valid. Both are deterministic. The second one is
*what was available at the budget* — useful for live UX where the
clock matters more than the row count.

## Why this matters

Most query systems give you two choices: wait for the full result
(server-side timeouts kill the query as an error) or pre-LIMIT the
work (which trades correctness for predictability — you might have
gotten the rows you wanted in another 5 ms). Neither matches the
shape of live UX: *"give me the best you have at this clock; if
that's incomplete, say so and I'll deal."*

ArcFlow's deadline-mode collapses the two: the query runs as
naturally as it would without the bound, and the *result itself*
carries the verdict. No client-side timeout race; no torn reads;
no LIMIT trick. Just `transport_outcome`.

## Run it

```bash
# Synthesise a small Hive-partitioned tree with mixed read costs
python 00-make-sample.py

# Run the same query under two budgets — observe the divergence
python 01-deadline.py
```

Expected output (illustrative — actual deadline behavior depends on
your machine's read latency):

```text
=== Generous deadline (5000 ms) ===
  rows returned:      47,832
  transport_outcome:  complete
  io_stats.bytes_read: 12,847,260
  io_stats.lane_used:  cpu_mmap
  wall time:           412 ms

=== Tight deadline (10 ms) ===
  rows returned:      6,914
  transport_outcome:  truncated
  io_stats.bytes_read: 1,938,432
  io_stats.lane_used:  cpu_mmap
  wall time:           11 ms
```

Both runs answer the same Cypher pattern. The first one is
complete; the second one is what was reachable in 10 milliseconds.

## When to use deadline-mode

| Pattern | When to use |
|---|---|
| **Frame-clock replay** (30 FPS, 33 ms per frame) | `deadline_ms = 30`; render what the engine has at the next frame boundary |
| **Live-broadcast ticker** (200 ms refresh) | `deadline_ms = 180`; reserve 20 ms for serialisation + render |
| **Partial-consensus aggregation** | `deadline_ms = N`; in the query body, mark `agreement_class = 'partial_at_deadline'` for the sources missing at deadline |
| **Bounded counterfactual exploration** | `deadline_ms = N`; the result carries which branches were explored |
| **Interactive analytics with budgeted latency** | `deadline_ms = N`; UI pattern "results so far (N rows seen)" |

## When NOT to use deadline-mode

| Pattern | Why not |
|---|---|
| **Reconciliation / audit queries** | Truncated results are wrong for "did this happen?" answers. Run to completion. |
| **Pre-commit validation queries** | A truncated check is no check. Run to completion. |
| **First-time count / sanity scan** | Use the footer-only count path (see [`virtual-labels-over-parquet`](../virtual-labels-over-parquet/) and [`lakehouse-count-fast-path`](../lakehouse-count-fast-path/)) — it's already sub-millisecond on millions of rows. |
| **Transactional writes** | Writes are atomic regardless; deadline applies to read paths. A truncated write is not a thing. |

## Substrate detail (one paragraph)

The deadline propagates from the SDK's `QueryOptions` through the FFI boundary into the engine's `DeadlineGuard`. The guard flows down to the reader's `ReadProvenance.deadline_ms`, which the [Smart Reader](/docs/concepts/layers/world-store-serve) consults at every range-fetch boundary. When the deadline fires, in-flight ranges complete; subsequent ranges are skipped; `TransportOutcome::Truncated` returns to the engine; the engine returns the partial result. The composition is deterministic for a snapshot — two queries with the same pattern, the same `deadline_ms`, against the same snapshot produce the same truncated rows.

## See also

- [Execution Options](/docs/worldcypher/execution-options) — the canonical reference for `QueryOptions`, `transport_outcome`, and `io_stats`.
- [World Store · Smart Reader](/docs/concepts/layers/world-store-serve) — the substrate that honors the deadline at the byte layer.
- [`lakehouse-count-fast-path`](../lakehouse-count-fast-path/) — the deadline-free fast path for pure `count(*)` queries.
- [`virtual-labels-over-parquet`](../virtual-labels-over-parquet/) — how virtual labels register a Lakehouse partition as a graph node class.
