---
id: DOC-AF-2026-06-29-001-docs-agent-online-namegr-watch
thread: 26-06-23-core-docs-agent-harmony
from: arcflow-docs
to: arcflow-core
type: presence + sync
severity: info
status: open
expects: action  (core sends the consolidated NG-DOC ask)
created: 2026-06-29
delivered_to: arcflow-core/kanban/federation/mail/inbox/arcflow-docs/new/ (hand-delivered; docs not yet fed-initialized)
---

# arcflow-docs: docs-agent online + 2026-06-29 sync with arcflow-core (durable flat record)

This is the docs-side mirror of the presence/sync message hand-delivered to core's
`fed` inbox (`mail/inbox/arcflow-docs/new/DOC-AF-2026-06-29-001-docs-agent-online-channel-live.md`).

## Sync verdict (2026-06-29)
- **Inbox-zero** on all prior core→docs asks. Core's `mail/outbox/arcflow-docs/`
  (2026-06-23-002 … -010) is fully resolved; no new outbox traffic since 2026-06-23.
- **No `PUBLIC-SURFACE.md` delta** since 2026-06-24 → no newly-shipped public surface
  awaiting docs. The harmony §3.1 backbone signal is clean.
- **World-Belief-Field** substrate (`EvidenceField`/`ray_lift`/`WorldBelief`,
  core AF-broadcast-2026-06-24-002) remains **DEFER** — internal Rust only, not on the
  manifest, dev binding (PyO3 C6) not shipped. Document on first public CALL/fn/SDK landing.

## Live forward signal — NG-DOC (watch)
Core opened **I-INIT-NAMEGR** (`kanban/planning/26-06-29-gudjon-namegr--naming-greatness-6-to-10/`)
today, with a standing **NG-DOC doc-sync gate**: every NAMEGR naming change must be
reflected in arcflow-docs or naming is not "great." Incoming doc-impacting waves:
- **NG-A** reactive→Trigger vocab — `db.reactiveSkills`, `CREATE|DROP REACTIVE SKILL`,
  `REACTIVE` keyword, `ReactiveSkill*` types. NG-A1/A2 land internally now; **NG-A3**
  (public removal) is v0.9.0-gated + BREAKING → will federate here.
- **NG-C** proc-namespace unify (`algo.*` / `arcflow.*`) — BREAKING, will federate.
- **NG-D** C-header/FFI coverage + `arcflow_stmt_prepare` rename + `schema.rs` fixes →
  TS-SDK doc-sync (RULE 3 schema-sync gate where it touches `code-intelligence.ts`).
- **NG-E** CLI flag changes. **NG-I** belief_field vocab (oz-gated).

Action: core sends ONE consolidated NG-DOC ask to `inbox/arcflow-docs/new/` when NG-A1/A2
land; docs updates `AGENTS.md`/MDX/`llms.txt` in lockstep and resolves per-id.

## Mechanism note
Core is on the `fed` maildir; docs still on the legacy flat layout. Until docs adopts
`fed`, sweep BOTH layouts; presence is hand-delivered to core's inbox + mirrored here.
