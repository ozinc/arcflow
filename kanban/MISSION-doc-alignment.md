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
  arcflow-core: main   # core agent merged docs/federation-alignment into main + deleted it (2026-06-23); core-side federation mirrors now commit on main and push to origin/main. NEVER disturb core's uncommitted engine-source edits (RULE 2).
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

## Arm C — Positioning alignment with oz-platform (operator directive 2026-06-23)

**Occasionally** (every ~3–4 iterations, and whenever authoring/upgrading a
positioning-bearing surface — hero lines, concept-page framing, the WME wedge,
README/llms positioning) run a **positioning-alignment pass** to keep the docs'
high-level positioning grounded in how OZ + ArcFlow are positioned company-wide.

**oz-platform IS available locally** at `/home/ozer/oz-platform` (git repo, has
`kanban/federation/`). This corrects the earlier "not cloned locally" note —
OZ-DOC federation can now be bilateral, and the positioning sources are readable
directly.

Grounding resources (read on a positioning pass):
- **Current positioning in market** — `oz-platform/apps/cloud/website` (107 MDXs).
  Lead sources: the world-model-thesis interview/blog posts under
  `content/blog/posts/en/general/` (e.g. `...world-model-thesis.mdx`,
  `...what-arcflow-is-really-building-toward.mdx`, `...the-five-layers.mdx`,
  `every-camera-is-an-intelligence-endpoint.mdx`), plus `apps/cloud/website/llms.txt`.
- **Positioning theory** — `oz-platform/kanban/references/knowledge-base/02-positioning-books-deep-concepts.md`
  (15 books, `DC-POSN-*` concepts). Use **Run Type A — Positioning Audit**:
  for each relevant `DC-POSN-*`, ask *"does our docs positioning violate or
  leverage this principle?"* and flag contradictions as action items. Cite
  `DC-POSN-*` IDs per the file's EARS triggers.
- **Discovery / customer-understanding** — `oz-platform/kanban/references/knowledge-base/07-Product-Discovery-Customer-Understanding-Leadership.md`
  (`DC-PDCL-*`). Pull discovery questions to interrogate our framing — real
  competitive alternative, status-quo-as-competitor, customer truth vs. our
  assumptions — and let the answers sharpen the docs' "why a developer reaches
  for this."

**Messaging invariant — de-emphasize "Rust" (operator 2026-06-23).** ArcFlow's
identity is **ultra-fast binaries** and striving to be **the industry's fastest
fully-featured operational world model engine** — not "written in Rust."
Implementation language is a detail, not the story. When describing what a
capability *is*, frame in outcomes (fast native code, edge/Tegra-viable, no GPU,
5 MB in-process binary), not the language. Keep "Rust" only where it's a genuine
SDK target (ArcFlow runs in Rust, Python, Node/WASM) — that's a binding, not the
identity. (Applied to information-layer.mdx, memory.mdx, AGENTS.md in the first
alignment pass.)

**Positioning-pass protocol:** (1) read the website positioning sources + this
repo's current positioning surfaces; (2) run the DC-POSN audit + DC-PDCL
discovery questions; (3) apply findings to docs positioning (keep the
records-not-simulates WME wedge as the invariant); (4) where docs reveal a
sharper frame than the market surface — or vice-versa — federate an `OZ-DOC-*`
message to `oz-platform/kanban/federation/` so positioning converges both ways;
(5) log findings (cite the `DC-*` IDs) in the progress log.

## Arm D — Git hygiene / sync (operator directive 2026-06-23)

**Occasionally** (end of an iteration batch, and before going idle) ensure git
is tidy and integrated across all touched repos (arcflow-docs, arcflow-core,
oz-platform):
- Worktree clean; nothing uncommitted (commit or stash with intent).
- All work committed on `docs/federation-alignment`.
- Branch pushed/synced to `origin`.
- Any open PRs merged.

**Operator sign-off (2026-06-23):** this supersedes the earlier "never push /
touch main without sign-off" guardrail for the push/sync/merge step — push and
merge are now authorized as routine hygiene. (Still: no engine *source* edits —
RULE 2 — and schema mirror changes need a paired core PR — RULE 3.)

**KNOWN BLOCKER (2026-06-23):** `git push` to `origin` for **arcflow-docs**
(`ozinc/arcflow`) returns **403** — the authed gh user `Gaurav-Gilalkar` lacks
push access to that repo (it CAN push `ozinc/arcflow-core`). arcflow-core branch
is pushed ✓. Until the operator grants docs-repo push access (or switches
credentials), the loop keeps committing arcflow-docs **locally** and re-surfaces
this blocker on each hygiene pass rather than retrying in a tight loop.

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
   oz-platform IS available at `/home/ozer/oz-platform` (read its website MDXs +
   the Arm-C grounding resources directly); federate an `OZ-DOC-*` message to
   `oz-platform/kanban/federation/` when a capability changes the market story.

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
| **World-Model Memory Engine** (I-INIT-0151) | **DONE (concept)** — `docs/concepts/memory.mdx` + AGENTS.md §Memory Engine + llms.txt (iter 3). Schema/signatures verified; staleness-as-validity + out-of-process semantic recall stated correctly; binding marked roadmap. Optional follow-on: a step-by-step guide. | done iter 3 | `crates/arcflow-core/src/worldgraph/memory.rs` (`write_memory_item`, `write_memory_version`+SUPERSEDES, `record_memory_provenance` CITES/CAUSED_BY, `recall_memories_about`/`recall_current_memories_about`/`recall_relevant_memories_about`); `crates/code-intelligence/src/memory_bridge.rs` (`ingest_with_memory`, `record_symbol_memory`); `crates/code-intelligence-parsers/src/lib.rs` (`parse_python`) |
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
- **2026-06-23 (iter 3)** — World-Model Memory Engine documented (biggest gap,
  flagship): new `docs/concepts/memory.mdx` (MemoryItem schema + ABOUT/SUPERSEDES/
  CITES/CAUSED_BY, staleness-as-validity, structural/current/hybrid recall,
  semantic recall correctly framed as out-of-process per ANTI-0020, the
  ingest_with_memory codebase world-model, runnable WorldCypher reading the memory
  graph). Schema/signatures verified against engine src; helpers Rust-only so
  binding marked roadmap. Registered in AGENTS.md (§Memory Engine) + llms.txt.
  Status `DOC-AF-2026-06-23-004` mirrored to core (proactive — WMM had no direct
  ask; shipped via broadcast a965fbbb).
- **2026-06-23 (queue add)** — Operator added **Arm C — positioning alignment**:
  occasionally ground docs positioning in oz-platform's website MDXs + the
  knowledge-base harnesses (`02` DC-POSN positioning books / Run Type A audit;
  `07` DC-PDCL discovery questions). Corrected stale note — oz-platform IS local
  at `/home/ozer/oz-platform` (git repo w/ federation), so OZ-DOC is bilateral.
  Wired into the loop as an occasional pass (~every 3–4 iters + on positioning
  surfaces). First positioning pass: next iteration.
- **2026-06-23 (queue add)** — Operator added **Arm D — git hygiene/sync** and
  authorized routine push/merge. Hygiene pass run: worktrees clean, all
  committed. `arcflow-core` branch **pushed to origin** ✓. `arcflow-docs` push
  **BLOCKED (403)** — authed gh user lacks push access to `ozinc/arcflow`;
  needs operator credential fix. No open PRs to merge.
</content>
- **2026-06-23 (iter 4)** — Clock-domain surface documented (AF-DOC-2026-06-12-001
  RESOLVED): `docs/temporal.mdx` §Querying AS OF a domain tick — `AS OF <domain>
  <tick>`, clock.register/advance/resolve, clock.resolve daemon method, floor-with-
  disclosure + 5 typed errors, EDGE-A2 durability caveat marked. Verified vs
  clock_domain_registry.rs + handlers_clock.rs. Closure DOC-AF-2026-06-23-005
  mirrored to core. Commit identity aligned to oz-platform (Gudjon Mar Gudjonsson
  <gudjon@oz.com>). Git diagnosis: docs-repo 403 is a repo-permission gap on the
  gh-authed account (Gaurav-Gilalkar lacks push on ozinc/arcflow; has it on
  oz-platform + arcflow-core) — NOT a local-config/passphrase issue.
- **2026-06-23 (iter 5)** — view.* push-stream surface documented (AF-DOC-2026-06-13-001
  RESOLVED): docs/protocol/jsonrpc-v1.md new "Live views (push streaming)" section —
  view.subscribe/credit/unsubscribe + view.delta notification, the 3 consumer must-knows
  (non-contiguous seq, credit backpressure + dropped_for_credit, duplex), framing caveat
  (newline default, --frame; P3.15 flip pending). Verified vs handlers_view.rs; method
  count 49→52. Closure DOC-AF-2026-06-23-006 mirrored to core. Also (separate ask): oz
  website C++ language scrubbed from ArcFlow positioning (branch fix/arcflow-drop-cpp-
  language pushed).
- **2026-06-23 (iter 6)** — Deterministic-replay contract documented (AF-DOC-2026-06-13-002
  RESOLVED): docs/temporal.mdx §Deterministic replay — the (query,seq)+pinned-version
  byte-identity guarantee, exact canonicalization (row sort by _id, verbatim string bytes,
  _created_at/_updated_at excluded, _confidence/_degree/_rel_types retained), per-version
  scope (no cross-version promise), on-result accessor marked "arrives with EDGE-A2".
  Verified vs edge_a5_replay_bit_identity.rs (FF-EDGE-06) + replay_digest.rs. Closure
  DOC-AF-2026-06-23-007 mirrored to core. Also: git identity normalized — all unpushed
  docs-branch commits + global config now Gudjon Mar Gudjonsson <gudjon@oz.com>.
- **2026-06-23 (topology + watch)** — arcflow-core merged docs/federation-alignment
  into main + deleted the branch; core-side mirrors now go on main (DOC-007 pushed to
  origin/main, b2b536bd..6bf7f776). Core agent has uncommitted engine edits incl. NEW
  crates/arcflow-runtime/src/info_procs.rs — likely the Information Layer GQL CALL
  surface. WATCH: when it ships, update docs/concepts/information-layer.mdx (+AGENTS.md)
  to promote the CALL surface from "roadmap" to shipped.
- **2026-06-23 (iter 7, Arm C — first positioning pass)** — Grounded docs positioning
  in oz-platform's world-model thesis + DC-POSN audit. Finding: docs led with the
  neural-vs-operational split; the real competitor is operational AMNESIA (DC-POSN-1.4).
  Fix: docs/concepts/world-model.mdx now opens with "digital world queryable 30 yrs;
  operational world remembered nothing — ArcFlow gives it persistent queryable memory"
  before the two-definition disambiguation (kept as evaluation-criteria control,
  DC-POSN-6.1/6.5; name/first-in-mind DC-POSN-5.3/5.4 intact; records wedge preserved).
  Federated DOC-OZ-2026-06-23-001 (pushed on oz-platform branch fed/doc-oz-positioning-
  2026-06-23) with a reciprocal rec: add the records-not-simulates wedge to the public
  engine page. Next Arm-C pass due ~iter 10-11.
- **2026-06-23 (iter 8)** — Drained 4 mail/outbox EDGE-B asks (all verified in source):
  cypher.execute_arrow (B4a) + per-view governance WITH(max_state_bytes,priority) +
  view.governance/_list (B3a) + event-time windows window.register_event_time/feed (B2a)
  → docs/protocol/jsonrpc-v1.md; provenance.bundle CALL (B8a) → AGENTS.md. Honest-scope
  caveats carried (single-batch arrow, GLOBAL refuse-to-grow, drop-only lateness, sentinel
  receipts/budget). Consolidated closure DOC-AF-2026-06-23-008 mirrored to core main.
  Remaining mail/outbox: executor Python SDK (B6a), install-time GPU admission (B7a),
  daemon readiness/recovery + memory-degradation operator contracts (06-13-004/007),
  view-replay re-sync (06-13-009).
- **2026-06-23 (WATCH FIRED — top next priority)** — core shipped the Information Layer
  GQL CALL surface: arcflow.info.{labelEntropy, labelRedundancy, labelKl, nodeSurprisal,
  nodeNcd} (commits 4182451b, 8dacb9c4 + more) with new fed(request) docs-needs on core
  main (66269d05, a0f75fd4, ...). NEXT ITERATION: promote docs/concepts/information-layer.mdx
  + AGENTS.md §Information Layer from "binding on roadmap" to SHIPPED for these 5 — add the
  CALL signatures (map: label_property_entropy→labelEntropy, label_property_redundancy→
  labelRedundancy, label_property_kl→labelKl, node_surprisal→nodeSurprisal, node_ncd→
  nodeNcd). KEEP "engine-level / not-yet-bound" only for the rest (information/similarity
  primitives, label_property_surprise, *_normalized) — verify exactly in source first.
  Close the new fed(request)s. THEN resume remaining mail/outbox EDGE asks (B6a executor
  SDK, B7a gpu-admission, daemon ops contracts, view-replay re-sync).
- **2026-06-23 (iter 9 — WATCH closed)** — Promoted Information Layer docs to the shipped
  CALL surface: docs/concepts/information-layer.mdx + AGENTS.md §Information Layer now show
  arcflow.info.{labelEntropy YIELD entropy_bits, labelRedundancy YIELD redundancy, labelKl
  YIELD kl_bits, nodeSurprisal YIELD surprisal_bits, nodeNcd YIELD ncd} as callable, with
  runnable examples; primitives (information/similarity) + label_property_surprise/_normalized
  kept engine-level. Verified vs info_procs.rs. Closed fed-requests 005/006/007 via
  DOC-AF-2026-06-23-009 (mirrored to core main).
- **2026-06-23 (TOP NEXT)** — arcflow-core filed reconciliation-event #1:
  mail/outbox/arcflow-docs/arcflow-core-2026-06-23-008-reconciliation-event-v1-public-surface-
  manifest. This is the harmony protocol's first reconciliation. NEXT: read the public-surface
  manifest, run a docs-side COVERAGE CHECK (every public symbol/capability has a docs entry),
  report gaps as federation tasks, confirm open TODO(docs-needs) count, reply on that thread.
- **2026-06-23 (iter 10 — RECONCILIATION EVENT #1)** — Ran docs-side coverage check vs
  arcflow-core/kanban/PUBLIC-SURFACE.md v1 (Information Layer scope). Result: 22/22 symbols
  documented = 100%. Gap found+fixed: label_property_entropy_bucketed + CALL
  arcflow.info.labelEntropyBucketed(label,key,buckets) YIELD entropy_bits were shipped but
  docs had bucketed as roadmap — now documented (info-layer.mdx + AGENTS.md; 6 CALL procs).
  Manifest finding reported to core: its CALL section omits labelEntropyBucketed (recommend
  add). Closed reconciliation -008 via DOC-AF-2026-06-23-010 (mirrored to core main). Open
  TODO(docs-needs) for Information Layer = 0. Harmony loop's first reconciliation: GREEN.
- **2026-06-23 (iter 11)** — Drained 2 more mail/outbox EDGE asks (verified in source):
  view.replay re-sync (B1, 06-13-009) → jsonrpc-v1.md §Live views (inclusive from_seq;
  gap:false replayed vs gap:true resume-floor; no auto-rematerialize); install-time GPU
  admission CREATE PROGRAM REQUIRES GPU(SM,VRAM) + program.spend (B7a, 06-14-009) →
  jsonrpc-v1.md §Programs (total-VRAM coarse, no cost meter, refuse-not-reroute). Method
  count 52→59. Closure DOC-AF-2026-06-23-011 mirrored to core main. REMAINING mail/outbox:
  arcflow.executor Python SDK (B6a, 06-14-006 — new SDK page), daemon readiness/recovery
  (A2b, 06-13-004) + memory-degradation (A3a, 06-13-007) operator contracts (deployment/
  daemon doc). Then: compression-reframe threading, sync/LAN naming, SSoT/version-cut.
- **2026-06-23 (iter 12 — TODO(docs-needs) annotation Inbox Zero + STANDING discipline)** —
  Operator directive: deep-groom TODO(docs-needs) in arcflow-core to Inbox Zero. Swept core:
  exactly 4 markers. 3 (replay_digest.rs:67, handlers_view.rs:46, handlers_view_replay.rs:40)
  already documented (iters 6/5/11) and being cleared by the core agent concurrently (staged).
  4th (readiness_signal.rs:3) documented THIS iter + flipped to DONE(docs-needs) by DOC (.rs
  annotation edits are in-scope per operator; Rust-logic no-edit rule unaffected). Shipped
  docs/deployment/daemon.mdx §"Operator contracts — readiness, recovery & memory" (A2b ask
  -004 + A3a ask -007, both with honest caveats). DOC-AF-2026-06-23-012 mirrored to core.
  **STANDING DISCIPLINE (added to loop): each cycle, re-sweep `grep -rn "TODO(docs-needs)"
  crates/` — for any new marker, deep-groom (read source + WHY), document at top standard,
  flip to DONE(docs-needs): DATE — <doc path> (Federation: DOC-AF id), and close bilaterally.
  Target: arcflow-core TODO(docs-needs) count stays at 0.**
- **2026-06-23 (iter 13)** — TODO(docs-needs) sweep: 0 (held). Manifest diff (manifest-b):
  info CALL grew to 7 procs — documented labelValueSurprise (binds label_property_surprise;
  YIELD surprise_bits) in info-layer.mdx + AGENTS.md; labelEntropyBucketed (ask -009) already
  done iter10. Info Layer CALL coverage 7/7 = 100%. Manifest broadened to worldgraph::memory
  section — confirmed 100% covered by memory.mdx (no new work). Family map (203 procs/32
  families) acknowledged; AGENTS.md is per-proc SSoT. Closed asks -009/-010 via
  DOC-AF-2026-06-23-013. NEXT: arcflow.executor Python SDK page (B6a), then compression-reframe
  threading, sync/LAN naming, SSoT/version-cut, + due positioning pass; future: family-map audit.
- **2026-06-23 (iter 14)** — Standing sweeps: TODO(docs-needs)=0; manifest unchanged since
  family-map (no new section). Documented arcflow.executor Python SDK (B6a, ask -006): new
  docs/guides/python-executor-sdk.mdx (Executor/@skill/SkillContext/EdgeOutput, UDS arcflow-llm
  wire, typed errors; edge-emitting core driveable-directly, engine-spawn marked B6b follow-up).
  Verified vs python/src/arcflow/executor/*. Registered in llms.txt. Closed -006 via
  DOC-AF-2026-06-23-014. REMAINING: compression-reframe threading (2026-06-23-002), sync/LAN
  named primitives, SSoT/version-cut catch-up (AF-DOC-2026-05-16-003), positioning pass (Arm C
  due), 203-proc family-map audit vs AGENTS.md.
- **2026-06-23 (iter 15 — Arm C + compression reframe)** — Standing sweeps green (TODO=0,
  manifest 100%). Threaded the 'store only the surprise' narrative through 3 capability pages,
  each anchored to a callable feature + linked to information-layer.mdx: causal-edges.mdx
  (confidence=−log₂p → nodeSurprisal), sync.mdx (WAL delta=residual coding), live-queries.mdx
  (view.delta=residual coding). No theory essays. Closes reframe ask -002 (DOC-AF-2026-06-23-015).
  Compression=intelligence framing now coherent across info-layer + 3 capability pages. REMAINING:
  sync/LAN named primitives (SyncTransport/ConcurrentStore sync server/executor-ring), SSoT/version-cut
  catch-up (AF-DOC-2026-05-16-003), 203-proc family-map audit vs AGENTS.md.
- **2026-06-23 (iter 16)** — Standing sweeps green (TODO=0, manifest 100%). Documented sync/LAN
  named primitives (proactive, Arm B): docs/sync.mdx new "LAN sync server" section (serve_sync
  over ConcurrentStore, POST /api/sync/push + GET /api/sync/pull?since=N; SyncTransport contract
  push/pull with MemoryTransport/OzWorldTransport; transports table named). docs/architecture/
  sync.mdx split shipped-LAN-server vs planned-cloud-API. Anti-vaporware: no HttpSyncTransport
  (verified). DOC-AF-2026-06-23-016 status mirrored to core main. REMAINING: SSoT/version-cut
  catch-up (AF-DOC-2026-05-16-003 conformance re-run), 203-proc family-map audit vs AGENTS.md.
- **2026-06-23 (iter 17)** — Standing sweeps green. SSoT/version-cut catch-up (AF-DOC-2026-05-16-003
  RESOLVED): re-ran sync-conformance-data.sh (from arcflow-core) + generate-reference.py — clean
  (version stripped, no 1.6.42, deprecated reactive gone; legit Reactive Write-Back Views EXT-0005
  page added), --check + lint-version-literals green, allowlist 3 entries already dropped. Caught
  docs conformance data up to engine current. Family-map audit (203/32): large families well-covered;
  THIN CALL-ref in AGENTS.md for arcflow.{vector,evidence,job,lag,world,temporal,graph} (+verify
  session/fusion) → NEW Arm-B backlog. Closed -003 via DOC-AF-2026-06-23-017.
  **STATUS: federation inbox + TODO(docs-needs) at Inbox Zero; family-map audit opened a fresh
  coverage backlog — NOT full Inbox Zero. NEXT: groom + document the thin CALL families in AGENTS.md.**
- **2026-06-23 (iter 18 — INBOX ZERO)** — Family-map coverage closed: AGENTS.md new
  "Additional CALL procedures (smaller families)" section covers all 32 manifest families —
  verified signatures for arcflow.lag.by_topic + counterfactual.branchAt; family-level coverage
  (engine capabilities-catalog one-liners) for vector/fusion/evidence/world/graph/temporal/
  session/job, with CALL arcflow.capabilities named as live SoT. **STATUS: INBOX ZERO —
  federation inbox drained, TODO(docs-needs)=0, manifest coverage 100% at tracked granularity.**
  Continuous-improvement tail: deepen per-proc YIELD for the 8 catalog-level families (1-2/cycle).
  DOC-AF-2026-06-23-018 mirrored to core. SHIFTING TO IDLE-POLL.
