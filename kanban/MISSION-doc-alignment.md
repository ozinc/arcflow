---
id: MISSION-doc-alignment
type: standing-mission
title: "Federation Inbox-Zero + Documentation-Greatness alignment with arcflow-core"
status: active
owner: arcflow-docs-agent
opened: 2026-06-23
operator: studio@oz.is
cadence: self-paced loop (drain backlog, then idle-poll arcflow-core for new commits)
working_branch:
  arcflow-docs: docs/federation-alignment
  arcflow-core: docs/federation-alignment
related:
  - "kanban/federation/FEDERATION.md (wire protocol)"
  - "kanban/federation/federation-membership.md (doctrine-translator role)"
  - "CLAUDE.md (boundary rules, doc conventions, RULE 3 schema sync)"
---

# Standing mission — keep arcflow-docs in lock-step with arcflow-core

ArcFlow's docs must represent the engine at its best, and stay aligned as the
engine ships. This mission has **two intertwined arms** plus an **always-on
discipline**, run as a self-paced loop until the backlog is drained, then as a
steady-state watcher.

## Arm A — Federation Inbox Zero (the named mission)

Bring `arcflow-core/kanban/federation/` to **Inbox Zero** for everything
addressed to `arcflow-docs-agent`: every open `AF-DOC-*` ask processed and
formally closed on **both** sides; every unacked version cut acknowledged; the
docs-side membership `lastConfirmed` kept current. Re-activate the channel
bidirectionally (mirror + ack + DOC-AF closure writes back into arcflow-core).

## Arm B — Documentation Greatness

Every shipped engine capability of the last 30 days documented to this repo's
quality bar (frontmatter `kind:`/`status:`, runnable WorldCypher, "See Also"
cross-refs, site-relative `/docs/...` links per P-93). No vaporware (see the
do-not-document list). The World-Model-Engine wedge ("records the real world;
neural models simulate") rides every new page.

## Always-on discipline — deep grooming BEFORE acting (operator directive 2026-06-23)

For EACH inbox item / capability, before writing a line of docs:
1. **Backlog refinement** — re-read the ask + this ledger; confirm it's still
   relevant, not superseded, not already covered.
2. **Codebase rooting** — read the engine source (path:symbol pointers below)
   until the surface is understood exactly: identifier spellings, error shapes,
   constraints. Confirm it is actually shipped in source (anti-vaporware).
3. **Understand the WHY** — capture the *purpose and reasoning* for the feature
   (read the planning dossier / wave file / PAT-* / broadcast that motivated it),
   not just the API. Docs explain why a developer reaches for it.
4. **oz-platform market-promise tie-in** — connect the capability to the
   public positioning we make on the oz-platform cloud/website/market surface.
   oz-platform is NOT cloned locally; derive the tie-in from positioning
   messages + this repo's positioning prose, and stage an `OZ-DOC-*` outbox
   note (mirrors when oz-platform is reachable) when a capability changes the
   market story.

---

## Per-iteration protocol (what the loop does each cycle)

```
1. SWEEP   ls/grep arcflow-core/kanban/federation for to:arcflow-docs + status:open,
           and for *cut* broadcasts newer than the last docs-side ack.
           Pick the highest-value unresolved item (priority order below).
2. GROOM   Run the deep-grooming discipline above for that item.
3. WRITE   Author/upgrade docs to the quality bar (concept + guide + AGENTS.md
           + llms.txt/llms-full.txt entries as needed). Wedge + oz tie-in.
4. CLOSE   Mirror the message into arcflow-docs/kanban/federation/; flip
           status open->resolved on both sides; write a DOC-AF-YYYY-MM-DD-NNN
           closure into arcflow-core. Refresh membership lastConfirmed.
5. LEDGER  Update this file: mark item done (commit SHA + files), append any
           newly discovered work.
6. COMMIT  Commit on docs/federation-alignment (and the core mirror branch).
           Do NOT push and do NOT touch main without operator sign-off.
```

**Scope guardrails (operator, 2026-06-23):** edit all prose surfaces
(docs/ MDX, AGENTS.md, llms.txt, llms-full.txt, CHANGELOG) but **NOT** version
pins (cookbook/install pins are an intentional target-end-state per CLAUDE.md
§URL-Discipline; bumping them is a separate operator decision). Never write
Rust/engine source (RULE 2). schema.rs mirror changes need a paired core PR
(RULE 3).

---

## CRITICAL — dual-inbox reality + harmony protocol (discovered 2026-06-23)

The federation channel has a **mechanism split** (core's harmony dossier
`00-PROTOCOL.md §7`, blocker #1). The loop MUST sweep **two** inbox layouts:

1. **Flat** — `arcflow-core/kanban/federation/AF-*.md` (legacy; what docs reads today).
2. **fed mail** — `arcflow-core/kanban/federation/mail/outbox/arcflow-docs/*.md`
   (core migrated to the `fed` tool; **12 doc-asks landed here unread**).

**Interim bridge (in effect):** core mirrors critical messages into our flat
format as `AF-CORE-YYYY-MM-DD-NNN-*.md` (first: `AF-CORE-2026-06-23-001`, docs
commit 95364a7). Both agents share the filesystem, so a local commit is
immediately visible — push is for durability, not delivery.

**Permanent fix (bilateral, at first reconciliation event):** EITHER (a) adopt
the `fed` tool + `mail/` layout here and `fed sync` core's outbox [core's
recommendation, cleaner], OR (b) core also emits flat. Until then: **the loop
reads both layouts.** DOC has ACKed the protocol (see DOC-AF-2026-06-23-002).

### Harmony protocol — DOC adopts (ref `arcflow-core/kanban/planning/26-06-23-core-docs-agent-harmony/00-PROTOCOL.md`)

- Engine is SSoT; docs is a one-way projection (provenance core → docs).
- Backbone signal: core publishes a machine-readable **public-surface manifest**;
  docs diffs it commit-over-commit for a lossless work list (vs lossy prose).
- Doc-relevant commits carry `Docs-Impact:` trailer + a `TODO(docs-needs):`
  handoff (SHA + signature + success criterion).
- Handshake: core opens → DOC acks → DOC writes doc commit → DOC resolves +
  federates `DONE(docs-needs)` back → core closes.
- Schema-sync (RULE 3) is the one hard-coupled SSoT; no-duplication rule:
  a concept lives in docs (public) XOR core kanban/AGENTS-ENGINE (internal).
- **Reconciliation event** per engine minor version: manifest published →
  DOC coverage check → confirm open `TODO(docs-needs)` == 0, schema CI green.
  Target metric: 100% public-symbol coverage.

## Arm A backlog — Federation Inbox (BOTH layouts; target: Inbox Zero)

| Item | Status | Action |
|---|---|---|
| `AF-DOC-2026-06-03-001` world-model-engine-positioning | **open** | Verify wedge across all surfaces (inventory: GOOD/consistent); mirror + resolve both sides. Linchpin: sets the positioning frame all Arm-B pages inherit. |
| `AF-DOC-2026-06-12-001` clock-domain surface (EDGE-A4) | open | Document `AS OF <domain> <tick>`, `CALL clock.register/advance/resolve`, typed errors. Home: temporal/time-travel + protocol ref. |
| `AF-DOC-2026-06-13-001` view.* push-stream (EDGE-A1) | open | Document `view.subscribe/credit/unsubscribe` + `view.delta` notification; the 3 must-understand behaviours (non-contiguous seq, credit backpressure, duplex). |
| `AF-DOC-2026-06-13-002` deterministic-replay contract (EDGE-A5) | open | Contract page; mark on-wire accessor "available from A2"; no cross-version identity promise. May stage until A2 — operator/AF acceptable. |
| `AF-DOC-2026-05-16-003` SSoT closure | open | Re-run sync-conformance-data.sh + generate-reference.py; confirm clean output; drop 3 conformance entries from lint-version-literals allowlist; resolve. |
| `AF-DOC-2026-05-16-007` threading-guide (resolved on core) | mirror-only | Verify docs-side page exists; mirror closure into docs inbox. |
| `AF-DOC-2026-05-17-008` typed-id contract (resolved on core) | mirror-only | Verify docs-side page exists; mirror closure into docs inbox. |
| Version-cut ack backlog | **stale** | Docs last acked `v0834`; core is **0.10.37**. Ack the cut span (single rollup ack acceptable) and refresh membership pin 0.8.1 -> 0.10.37. |
| `AF-CORE-2026-06-23-001` info-layer + reframe + harmony | **acked** | Harmony protocol adopted (DOC-AF-2026-06-23-002). 3 asks split into Arm B (info-layer docs), positioning reframe, harmony adoption. |

### Arm A backlog — fed `mail/outbox/arcflow-docs/` (12 unread asks from the mechanism split)

| Item | Maps to Arm B capability |
|---|---|
| `2026-06-23-003` information-layer-shipped public API | Information-theory / compression (concept + per-capability wording from core `01-FEATURE-SET.md`) |
| `2026-06-23-002` reframe developer-capability docs (compression=intelligence) | Positioning reframe — proof layer beneath "World Model Engine" |
| `2026-06-23-004` harmony protocol proposal | ACKed (DOC-AF-2026-06-23-002) |
| `2026-06-13-009` view-replay re-sync wire surface (EDGE) | folds into `view.*` / replay docs |
| `2026-06-13-012` event-time-window wire surface (EDGE-B2a) | windows/watermark page |
| `2026-06-14-002` per-view governance wire surface (EDGE-B3a/b) | LIVE clause `WITH (max_state_bytes, priority)` |
| `2026-06-14-004` arrow-ipc result lane `cypher.execute_arrow` (EDGE-B4a) | protocol/reference |
| `2026-06-14-006` `arcflow.executor` Python SDK (EDGE-B6a) | executor SDK page |
| `2026-06-14-009` install-time GPU admission + program spend (EDGE-B7a) | governance/deployment |
| `2026-06-14-010` provenance.bundle CALL (EDGE-B8a) | procedures reference |
| `2026-06-13-004` daemon readiness/recovery operator contract | deployment/daemon ops |
| `2026-06-13-007` daemon memory-degradation operator contract | deployment/daemon ops |

## Arm B backlog — Capability documentation (source: 30-day arcflow-core feat commits)

Priority by gap size × flagship value. Verdicts from the 2026-06-23 coverage audit.

| Capability | Coverage | Target docs | Engine source-of-truth |
|---|---|---|---|
| **World-Model Memory Engine** (I-INIT-0151) | **NONE** | new `docs/concepts/memory.mdx` + `docs/guides/world-model-memory.mdx`; `### Memory` in AGENTS.md after Code Intelligence API; llms.txt Python surface | `crates/arcflow-core/src/worldgraph/memory.rs` (`write_memory_item`, `write_memory_version`+SUPERSEDES, `record_memory_provenance` CITES/CAUSED_BY, `recall_memories_about`/`recall_current_memories_about`/`recall_relevant_memories_about`); `crates/code-intelligence/src/memory_bridge.rs` (`ingest_with_memory`, `record_symbol_memory`); `crates/code-intelligence-parsers/src/lib.rs` (`parse_python`) |
| **Information-theory / compression** ("compression = intelligence") | **DONE (concept)** — `docs/concepts/information-layer.mdx` + AGENTS.md §Information Layer + llms.txt; signatures verified; binding marked roadmap. Reframe threading through existing pages still open (ask -002). | done iter 2 | `crates/arcflow-core/src/information.rs`, `similarity.rs` (`ncd`, `ncd_similarity`), `graph_information.rs` (`label_property_entropy`, `node_surprisal`, `node_ncd`, `label_property_kl`), `mape_flywheel.rs` (SSoT) — **Rust-only, no Cypher CALL surface yet** |
| **Sync / LAN named primitives** | **THIN/GOOD** (drift) | extend `docs/sync.mdx` + `docs/architecture/sync.mdx`; new `### Sync / LAN` in AGENTS.md | `crates/arcflow-runtime/src/sync_server.rs` (`serve_sync`, `POST /api/sync/push`, `GET /api/sync/pull?since=N`), `sync_transport.rs` (`SyncTransport` trait), `crates/arcflow-storage/src/sync_engine.rs` |
| **Executor-ring / IPC** (I-INIT-0105) | NONE | new section under deployment/architecture | `crates/arcflow-runtime/src/executor_client.rs` (`ShmRing`, `dispatch_shm`, `dispatch_shm_poll`), `bin/arcflow-echo-sidecar.rs` |
| **EDGE clock-domain / view.* / replay** | NONE | see Arm A items 2–4 (filed as doc-asks) | per Arm A |
| **Arrow IPC result lane** (EDGE-B4a) | NONE | reference/protocol | daemon `cypher.execute_arrow` |
| **Per-edge provenance bundle** (EDGE-B8a) | NONE | reference/procedures | `CALL provenance.bundle(relId) YIELD ...` |
| **Per-view governance** (EDGE-B3a/b) | NONE | worldcypher LIVE clause | `live_statements.rs` `WITH (max_state_bytes, priority)`; `view.governance` |
| **OTLP/HTTP trace exporter** | NONE | observability/deployment | `crates/arcflow-runtime/src/otel.rs` (`SpanRecorder.flush_to_otlp`), `otlp_export.rs` |
| **Tegra/CUDA dispatch thresholds** | n/a | low priority — internal perf, no public API | — |

## DO-NOT-DOCUMENT (anti-vaporware, confirmed not shipped/reachable)

- WMM **semantic/HNSW recall + distillation** (TranscriptSegment→FactDelta) — gated on an embedding model.
- Info-theory primitives have **no Cypher CALL surface** — document as Rust/SDK APIs only.
- **No `HttpSyncTransport` type** — swarm-LAN uses `lan_discovery` + ws.
- **Per-label lake-retention** (EDGE-B10a) — recorded POLICY/contract only, no actuator.
- Deterministic-replay **on-wire `(plan_version, engine_version)` accessor** — engine-internal until EDGE-A2.
- view.* **P3.15 framing-default flip** — not yet shipped; default framing is `newline`, length-prefix is `--frame`-selectable.

---

## Progress log

- **2026-06-23 (iter 1)** — Mission opened. Inventory complete (core feat
  commits ×30d + docs coverage audit). Branches cut in both repos. Ledger
  authored. Channel re-activated: `AF-DOC-2026-06-03-001` (positioning) closed
  bilaterally; 4 open AF-DOC asks mirrored + acked; membership refreshed
  (engine 0.10.37). Closure `DOC-AF-2026-06-23-001` mirrored to core. Commits:
  docs (pending), core `a9bd4083`.
- **2026-06-23 (iter 1, cont.)** — Discovered the **federation mechanism split**
  via inbound `AF-CORE-2026-06-23-001` (docs 95364a7): core migrated to the
  `fed` tool; **12 doc-asks** sat unread in `mail/outbox/arcflow-docs/`.
  Adopted core's harmony protocol; recorded dual-inbox sweep + 12 asks into
  Arm A/B backlog. ACK staged as `DOC-AF-2026-06-23-002`.
- **2026-06-23 (iter 2)** — Information Layer documented (ask `2026-06-23-003`
  RESOLVED): new `docs/concepts/information-layer.mdx` (surprise/entropy/KL/NCD,
  graph self-measurement, compression=intelligence beneath the WME category),
  signatures verified against engine source, binding marked roadmap (anti-
  vaporware). Registered in AGENTS.md + llms.txt. Reframe ask `2026-06-23-002`
  IN PROGRESS (foundation laid; cross-capability threading pending). Closure
  `DOC-AF-2026-06-23-003` mirrored to core.
</content>
