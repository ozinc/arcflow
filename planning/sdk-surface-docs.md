# SDK Surface Wave — Documentation Plan

This file tracks what documentation to write, in which repo, and what it's
blocked on. Mirrors the implementation plan at:
`arcflow/planning/26-04-09-sdk-surface/AGENTS.md`

---

## DONE(invariant): 2026-05-05 — alpha target-state rule supersedes the "no unimplemented APIs" gate.

The original invariant said "Write docs for what exists. Never describe unimplemented APIs." That gate was relaxed during alpha — see `~/.claude/projects/-Users-gudjon-code-arcflow-docs/memory/feedback_docs_describe_target_state.md`. Public-facing docs may now describe target-state behavior of features in alpha scope; testers report doc-vs-engine deltas as feedback signal. When ArcFlow exits alpha, this gate may be reinstated.

## NOTE(invariant): BASAL Pro concerns stay out of arcflow-docs.

These items are BASAL Pro concerns, not ArcFlow engine concerns, and therefore get NO documentation in arcflow-docs even under the alpha target-state rule (they are out of scope, not just unshipped):

- DSL Framework (LegalQuery / FinanceQuery / TaxQuery)
- Domain SDL (runtime node/edge type registration)

If these appear in an arcflow-docs PR, reject it.

**Why:** Repo-boundary discipline (RULE 1) — these belong in their owner's repo. The alpha relaxation only applies to features that ARE in ArcFlow's scope; out-of-scope features stay out regardless of ship status.

---

## What Already Has Docs (No Action Needed)

| Feature | Current Doc | Status |
|---------|------------|--------|
| Z-set delta / LIVE MATCH / CREATE LIVE VIEW | `docs/live-queries.mdx` | Complete |
| DeltaEvent, LiveQuery, SubscribeOptions types | `docs/reference/types.mdx` | Complete |
| AS OF temporal queries | `docs/temporal.mdx` | Complete |
| Graph algorithms (27+) | `docs/algorithms.mdx` | Complete |
| Workspace CLI (arcflow workspace init) | `docs/guides/filesystem-workspace.mdx` | Complete |
| Proof artifacts (snapshot-based) | `docs/concepts/proof-artifacts.mdx` | Complete |
| Skill GQL syntax | `docs/skills/create-skill.mdx` | Complete |

---

## SDK Surface Wave — Per-Item Status (as of 2026-05-05)

| Item | Status | Notes |
|---|---|---|
| DOC-01 Subscription Guide | **DONE(wave-A): 2026-05-05** | `db.subscribe()` shipped; documented in `docs/reference/api.mdx:121`, `AGENTS.md` API surface, `llms.txt`, `llms-full.txt`. `DeltaEvent` / `LiveQuery` / `SubscribeOptions` types in `docs/reference/types.mdx`. |
| DOC-02 Temporal API + Provenance Chain | TODO(wave-A) | `db.queryAt()` (snapshot-URI form) shipped and documented. `db.queryAsOf(cypher, timestamp)` and `db.provenanceChain()` typed wrappers — pending. |
| DOC-03 Workspace Programmatic API | TODO(wave-A) | `db.workspace.*` napi-rs binding not yet shipped. |
| DOC-04 Skill Registration API | TODO(wave-A) | `db.registerSkill()` napi-rs binding not yet shipped. |
| DOC-05 Live Proof Registration API | TODO(wave-A) | `db.registerLiveProof()` not yet shipped. |
| DOC-06 Algorithm Configuration API | TODO(wave-A) | `db.runAlgorithm(AlgorithmConfig)` typed dispatch not yet shipped. CALL-procedure form is the current path. |

For TODO items below: the bindings haven't shipped yet, so the original "do not write these docs before the napi-rs bindings exist — the API surface may shift" still applies. The alpha target-state relaxation in the rewritten invariant above does **not** override this — wave-A is explicitly held until SDK shape stabilises.

---

### DOC-01: Programmatic Subscription Guide ✅ DONE(wave-A): 2026-05-05

**Blocked on:** SDK-01 (`subscribe() / unsubscribe()` napi-rs re-export) — **shipped.**

**Where:** New section in `docs/live-queries.mdx` — after the existing "Legacy Live Queries" section.
Or a new `docs/guides/subscription-api.mdx` if the content warrants a full page.

**What to cover:**
- `db.subscribe(query, handler, options)` — TypeScript SDK call
- `DeltaEvent.added` / `DeltaEvent.removed` — edge-triggered, not level-triggered
- `DeltaEvent.frontier` — monotonic sequence number for ordering
- `lq.cancel()` — cleanup pattern
- Pattern: Routine layer — subscribe once on startup, let deltas drive work
- Pattern: Geofence — spatial predicate in query, enter/exit via added/removed
- Pattern: Agent task queue — subscribe to `Task` nodes WHERE status = 'pending'

```typescript
// Routine layer pattern (Minimal Example)
const lq = db.subscribe(
  "MATCH (t:Task) WHERE t.status = 'pending' RETURN t.id, t.type, t.payload",
  (event) => {
    for (const row of event.added)   queue.push(row)
    for (const row of event.removed) queue.cancel(String(row.id))
  }
)
// Stays active for the process lifetime — cancel on shutdown
process.on('SIGTERM', () => lq.cancel())
```

**NOTE(invariant): Do not describe WebSocket push (FR-07) in this doc.**
Reason: FR-07 is Phase 2. The polling-based subscribe() is the current API.
When push ships, it adds an optional `{ transport: 'websocket' }` in options.
The existing examples remain valid.

---

### DOC-02: Temporal API + Provenance Chain

**Blocked on:** SDK-02 (`queryAsOf()` + `provenanceChain()` typed wrappers)

**Where:** New section at the bottom of `docs/temporal.mdx`

**What to cover:**
- `db.queryAsOf(cypher, timestamp, params?)` — typed wrapper over AS OF
- `db.provenanceChain(nodeId, maxDepth?)` — walk from a node back to its origin
- `ProvenanceNode` shape: skillName, version, confidence, tick, sourceFacts
- Pattern: "Who created this relationship and when?"
- Pattern: "What did the graph look like at seq N?"
- Pattern: "Which facts supported this inference?"

```typescript
// Who created this and when?
const chain = db.provenanceChain('node_42', 3)
for (const node of chain) {
  console.log(`${node.skillName} v${node.skillVersion} @ tick ${node.tick}`)
  console.log(`confidence: ${node.confidence}, from: ${node.sourceFacts.join(', ')}`)
}

// Point-in-time read
const snapshot = db.queryAsOf(
  "MATCH (p:Person {id: $id}) RETURN p.name, p.role",
  yesterday,
  { id: 'person_99' }
)
```

---

### DOC-03: Workspace Programmatic API

**Blocked on:** SDK-03 (`WorkspaceRouter` napi-rs binding)

**Where:** New section in `docs/guides/filesystem-workspace.mdx`
("Programmatic API" section after the existing CLI section)

**What to cover:**
- `db.workspace.create(id, options?)` — create a new isolated workspace
- `db.workspace.use(id)` — scope subsequent queries to a workspace
- `db.workspace.grant(workspaceId, actor, role)` — access control
- `db.workspace.list()` — enumerate workspaces
- Pattern: multi-tenant SaaS — one workspace per customer
- Pattern: test isolation — create workspace per test suite, drop after

```typescript
// Multi-tenant pattern
const tenantDb = db.workspace.create(`tenant-${orgId}`, { isolationLevel: 'partition' })
tenantDb.workspace.grant(`tenant-${orgId}`, userId, 'write')
tenantDb.workspace.use(`tenant-${orgId}`)
tenantDb.mutate("CREATE (n:Document {id: $id})", { id: docId })

// Test isolation
const testDb = db.workspace.create(`test-${Date.now()}`)
// ... run tests ...
testDb.workspace.drop(testDb.workspace.id)
```

---

### DOC-04: Skill Registration API

**Blocked on:** SDK-04 (`registerSkill()` napi-rs binding)

**Where:** New section in `docs/skills/create-skill.mdx`
("TypeScript Registration API" section after the existing GQL section)

**What to cover:**
- `db.registerSkill(spec)` — SYMBOLIC skill registration without raw GQL
- `SkillSpec` shape: name, version, tier, allowedLabels, deriveFn
- `DeriveFn` signature: (source, candidates) → results
- `db.listSkills()` — introspect registered skills
- Pattern: domain-level registration (not hardcoded in query strings)

```typescript
db.registerSkill({
  name: 'employment_linker',
  version: 4,
  tier: 'SYMBOLIC',
  allowedLabels: ['Person', 'Organization'],
  deriveFn: (source, candidates) => {
    return candidates
      .filter(c => c.get('industry') === source.get('industry'))
      .map(c => ({
        toId: String(c.get('id')),
        relType: 'WORKS_AT',
        confidence: 0.82,
        properties: { start_date: source.get('hire_date') }
      }))
  }
})
```

**NOTE: LLM tier (`tier: 'LLM'`) will throw `LLM_TIER_NOT_YET_IMPLEMENTED`
until that tier ships. Document the error; do not document LLM tier usage.**

---

### DOC-05: Live Proof Registration API

**Blocked on:** SDK-05 (`registerLiveProof()` wired to ConcurrentStore)

**Where:** New section in `docs/concepts/proof-artifacts.mdx`
("Continuous Verification" section — contrast with the existing snapshot proofs)

**What to cover:**
- `db.registerLiveProof(spec)` — attach a standing assertion to the graph
- `LiveProofSpec`: name, assertion (GQL), predicate, onViolation
- `LiveProofHandle`: status(), lastChecked(), cancel()
- Contrast with snapshot proofs: continuous watch vs point-in-time check
- Pattern: data quality gate — "no Fact node may have confidence < 0.1"
- Pattern: referential integrity — "every WORKS_AT edge must have a valid Person on both sides"

```typescript
const proof = db.registerLiveProof({
  name: 'confidence_floor',
  assertion: 'MATCH (f:Fact) WHERE f.confidence < 0.1 RETURN f.id',
  predicate: { type: 'rowCount', max: 0 },   // must return zero rows
  onViolation: 'warn'
})

console.log(proof.status())      // 'passing' | 'failing' | 'unknown'
console.log(proof.lastChecked()) // epoch ms
```

---

### DOC-06: Algorithm Configuration API

**Blocked on:** SDK-06 (`runAlgorithm(AlgorithmConfig)` dispatch, PageRank param exposure)

**Where:** New section in `docs/algorithms.mdx`
("TypeScript SDK" section — supplement the existing CALL procedure reference)

**What to cover:**
- `db.runAlgorithm(config)` — typed dispatch without raw CALL strings
- `AlgorithmConfig` discriminated union — show key algorithms with their params
- `db.runAlgorithmLive(config)` — incremental version (6 supported algorithms)
- Key configurable parameters: PageRank damping + iterations, Louvain resolution
- Note: GPU dispatch is automatic — no manual override

```typescript
// PageRank with custom damping
const scores = db.runAlgorithm({
  algorithm: 'pageRank',
  damping: 0.75,      // default 0.85
  iterations: 30      // default 20
})

// Domain-specific relationship strength
const strength = db.runAlgorithm({ algorithm: 'relationshipStrength' })

// Live (incremental) community detection
const liveComm = db.runAlgorithmLive({ algorithm: 'louvain', resolution: 1.2 })
liveComm.cancel()   // when done
```

---

## After All Six Ship

Update `llms.txt` and `llms-full.txt` to include the new TypeScript SDK methods.
Update `AGENTS.md` to add the new API calls to the "Quick start" and "API surface" sections.
Update `docs/reference/api.mdx` with the full interface additions.

---

## What Stays Out of This Repo

| Item | Reason |
|------|--------|
| DSL Framework | BASAL Pro concern — not an ArcFlow API |
| Domain SDL | BASAL enforces its schema in TypeScript |
| SDK implementation details | Lives in `arcflow/planning/26-04-09-sdk-surface/` |
