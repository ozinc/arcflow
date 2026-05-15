# Algo-Trading World Model

> **The persistent, queryable, replayable operational world model your
> trading agent reads, writes, and remembers from.**

**Audience:** quant developers · ML engineers · LLM-agent builders
**Runtime:** under 3 minutes total
**Pins:** `oz-arcflow==0.8.0`

## The four hard problems this addresses

An LLM-driven trading agent has to solve four engineering problems that
are individually doable in a weekend and collectively a nightmare to
integrate. Most stacks bolt together five or six systems (vector DB +
SQL/timeseries + message bus + scheduler + audit log + feature store)
and pay the drift tax forever. The list, with the symptom each one
ships in production when it goes wrong:

1. **Reconstructing decision-time state without look-ahead bias.** Six
   weeks after a trade, the auditor asks "what fundamentals were
   visible at decision time?" Standard databases store current state
   only. Reconstructing the decision-time view means correlating an
   audit log, a version table, and denormalized snapshots — three
   sources that drift the moment someone forgets to update one. The
   bug surfaces as a strategy that backtested at 1.8 Sharpe and lives
   at 0.4.

2. **Backtest-vs-live equivalence.** The strategy is written in pandas
   for backtest, then rewritten in a streaming framework for live, and
   the team prays they produce identical results. They don't, because
   pandas computed `lag(close, 1)` over the full table while the
   streaming version maintained a sliding window — same semantics in
   theory, off-by-one bugs in practice. Most of the alpha decay
   between sim and live comes from this gap, not from market regime
   change.

3. **Confidence-weighted multi-source fusion.** Technical signals come
   out of a deterministic pipeline at high confidence. LLM-emitted
   sentiment scores come out at 0.4–0.7 with high variance. ML regime
   classifiers emit forward beliefs at mid confidence. Stitching these
   into a single decision means a JOIN chain across four schemas, each
   with its own confidence column, each silently mistyped when someone
   refactors. The agent ends up trusting `sentiment_score > 0.5` as if
   it were a deterministic signal, because the trust tier was lost in
   the JOIN.

4. **Maintained context for the agent's prompt.** Each prompt turn
   wants fresh sector rollups, cross-sectional ranks, top-of-sector
   leaders. Recomputing in Python every turn is wasteful. Pre-computing
   with a scheduler creates drift between the scheduler's view and the
   live agent's view — the prompt sees a 30-second-stale percentile
   rank while the agent's decision is sized against the live price. The
   strategy looks confused; the bug is a freshness mismatch nobody
   traced.

Each one is solvable in isolation with enough engineering. Solving all
four in one architecture is what an operational world model is for.
This recipe builds one in three minutes.

## What an operational world model is

An operational world model is a persistent store of *what is actually
happening* in some domain, with three epistemic states first-class on
every fact:

- **observed** — directly measured. Trades from the tape, OHLCV bars,
  fundamentals filings, the agent's own decisions. `_confidence ≥ 0.95`.
- **inferred** — derived by reasoning over observed facts. Rolling
  stats, cross-sectional ranks, sector aggregations, technical signals
  computed from prices. `_confidence 0.70–0.85`.
- **predicted** — model output. LLM sentiment scores, HMM regime
  beliefs, ML forward forecasts. `_confidence 0.30–0.70`.

The trading agent is not just *reading* a world model. It **writes its
own decisions back into it** — `TradeDecision` nodes become first-class
entities in the same graph as the evidence those decisions were based
on. `AS OF seq` replay six weeks later returns "what did I know, what
did I think, and what did I decide" together, deterministically. That
single property is the audit trail every regulator wants and the
dataset every causal-inference model wants. They are the same dataset.

## Three patterns this recipe ships

### Step 1 — Persistent memory · `AS OF seq` replay

```python
db.execute("CREATE (t:TradeDecision {ticker:'ENGY-02', action:'BUY', ...})")
db.execute("MATCH ... SET f.eps = 2.10")
db.execute("MATCH ... SET f.revision = 'restated-day-35'")

# What did the agent see at decision time?
db.execute(
    "MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f) "
    "AS OF seq $s RETURN f.eps, f.revision",
    params={"s": 1},
)
# → original eps, original revision. Bit-for-bit what was visible
# before the restatement entered the WAL.
```

The canonical look-ahead-bias landmine: a mid-period earnings
restatement makes "what fundamentals were visible at decision time"
ambiguous in most systems. Here it's one line. Decisions and evidence
live in the same graph, queried the same way. Bulk ingest
(`bulk_create_*`) vs `execute()` is the auditability boundary — cold
history bypasses the WAL, decisions and revisions enter it. Every seq
in the WAL is meaningful.

### Step 2 — Orchestrated context · the graph IS the working memory

```python
SECTOR_ROLLUP    = "MATCH (b:DailyBar) WHERE b.day_idx = $day ..."
CROSS_RANK       = "MATCH (b:DailyBar) WHERE b.day_idx = $day RETURN ..., percent_rank() OVER (PARTITION BY b.sector ORDER BY b.close) ..."
LEADERS_BY_SECTOR = "MATCH (b:DailyBar) ... RETURN ..., row_number() OVER (PARTITION BY b.sector ORDER BY b.close DESC) AS rn"

for tick in ticks:
    insert_bar(tick)
    rollup, ranks, leaders = (list(db.execute(q, params={"day": tick.day}))
                              for q in (SECTOR_ROLLUP, CROSS_RANK, LEADERS_BY_SECTOR))
    feed_to_agent_prompt(rollup, ranks, leaders)
```

Three context queries; one MATCH each. The graph is the orchestration
substrate — no external scheduler, no factor-rollup job, no message
bus. Window functions (`lag`, `percent_rank`, `row_number`, `OVER
(PARTITION BY … ORDER BY …)`) are full WorldCypher citizens. The same
query shape runs in batch, in a per-tick polling loop, and as a
maintained `LIVE VIEW` — the engine's Z-set algebra substrate
guarantees the three modes are operator-plan-equivalent.

### Step 3 — Evidence-algebra fusion · one MATCH, every trust tier

```cypher
-- AGREEMENT: technical + sentiment, same direction
MATCH (s:Symbol)-[:EMITS]->(sig:Signal),
      (s)-[:MENTIONS]->(news:NewsSentiment)
WHERE sig.day_idx = news.day_idx AND sig.score * news.score > 0
RETURN s.ticker,
       sig.score * sig._confidence + news.score * news._confidence AS fused_score
ORDER BY fused_score DESC

-- DISAGREEMENT: same MATCH, flipped predicate
WHERE sig.day_idx = news.day_idx AND sig.score * news.score < 0

-- THREE-SOURCE: layer in HMM regime beliefs, same shape
MATCH (s)-[:EMITS]->(sig:Signal), (s)-[:REGIME_FOR]->(reg:RegimeBelief)
WHERE sig.day_idx = reg.day_idx AND reg.regime = 'trending' AND sig.score > 0.03

-- TRUST-TIER: only facts with confidence ≥ 0.6
WHERE sig._confidence >= 0.6
```

`_observation_class` and `_confidence` are on every node and edge.
Technical signals at `observed`/0.95 coexist with LLM-emitted sentiment
at `predicted`/0.45 and HMM regime beliefs at `predicted`/0.65 in one
graph. The same MATCH shape spans agreement, disagreement, three-source
cross-checks, and trust-tier filters. Swapping a single predicate is
the entire delta. When the next signal source arrives — options-flow
detection, satellite-imagery scores, analyst-call transcript extraction
— it writes facts into the same graph and every existing fusion query
absorbs it automatically.

## Run

```bash
uv sync
uv run python 01-persistent-memory.py
uv run python 02-orchestrated-live-context.py
uv run python 03-confidence-weighted-fusion.py
```

`_load.py` is the shared fixture: 8 symbols × 60 days OHLCV
(`observed`), fundamentals with a planted restatement landmine on
`ENGY-02` at day 35 (`observed`), 6 news-sentiment events from two
distinct LLM sources (`predicted` at 0.40–0.70), and 4 HMM regime
classifications per symbol (`predicted` at 0.55–0.75). Loads in under a
second.

## Capabilities exercised

| Capability | Surface |
|---|---|
| `AS OF seq $param` — temporal replay with snapshot isolation | WorldCypher; persisted-WAL backed |
| Window functions (`lag` · `lead` · `percent_rank` · `row_number`) with `OVER (PARTITION BY … ORDER BY …)` | WorldCypher; Z-set window operator |
| `_observation_class` + `_confidence` first-class on every node and edge | Data model; written by every write path |
| Two-tier ingest as the auditability boundary | `bulk_create_nodes` / `bulk_create_relationships` (no WAL) vs `execute()` (WAL, one monotonic seq per call) |
| `CREATE LIVE VIEW` · `LIVE CALL` · view chaining · continuous-proof | WorldCypher; Z-set incremental-computation substrate |

## See also

- [`agent-knowledge-base`](../agent-knowledge-base/) — confidence-scored GraphRAG retrieval over a small document corpus
- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the operational world model applied to 60Hz spatial tracking
- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — `AS OF seq` patterns across fraud, robotics, IoT
