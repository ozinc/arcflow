---
id: arcflow-docs-agent-presence
type: agent-presence-registry
title: "Active agent sessions in arcflow-docs"
lastUpdated: 2026-06-29
related:
  - "AF-broadcast-2026-05-16-federation-mechanics-proposal.md (the protocol this registry follows)"
---

# Active agent sessions in arcflow-docs

Per the federation-mechanics proposal, each repo maintains a presence registry for active /loop sessions. `arcflow-docs` is mostly single-session work (the docs surface is one set of files; concurrent sessions would race more than they help), so the build-owner role is trivially this session's.

## Active sessions

| Session ID | Started | Scope (DDD bounded contexts) | Build owner | Status |
|---|---|---|---|---|
| doc-session-2026-06-29 | 2026-06-29 | Standing doc-alignment `/loop` (mission steady-state). Synced with arcflow-core federation 2026-06-29: inbox-zero confirmed, `PUBLIC-SURFACE.md` delta clean, WBF held on DEFER. **Fed-initialized the docs↔core channel** — hand-delivered docs-agent-online presence to core `mail/inbox/arcflow-docs/new/` + registered peer in core `.sync-state.json`. Watching inbound **NG-DOC** (NAMEGR naming-change waves: reactive→Trigger, proc-namespace unify, C-header/FFI, CLI flags). | **yes** | active |
| doc-session-2026-05-18T12:37:00Z | 2026-05-18 12:37Z | Top-level docs surface — README.md, AGENTS.md, llms.txt, llms-full.txt, ARCFLOW_FOR_AI_AGENTS.md, LICENSE-CORE / LICENSE-FAQ, ROADMAP, CHANGELOG, REPO-SPLIT. Operator brief: "make sure all documentation is at top level, and also the README." Pulled-in from the substantial uncommitted working tree (~100+ files modified across 2026-05-17/18) — first task: triage what's safely committable. | **yes** | active |
| ~~doc-session-2026-05-16T05:30:00Z~~ | 2026-05-16 05:30Z | Federation triage, 8-layer doctrine adoption, PAT-0050 brand-stack reframe, cookbook authoring, hero-page reframe | (was yes) | completed (rolled over; commits 7f2e868..06590f9 + 100+ uncommitted working-tree edits inherited by next session) |

## Build-owner scope (this session)

Per the proposal — what the `arcflow-docs` build-owner owns:

- `scripts/sync-conformance-data.sh` invocations (pulls conformance data from `~/code/arcflow-core`).
- `scripts/generate-reference.py` runs (regenerates MDX reference pages from synced data).
- `scripts/lint-version-literals.py` allowlist edits.
- `scripts/check-schema-sync.js` invocations.
- `typescript/src/code-intelligence.ts` schema-mirror updates (the mirror side of the engine's `schema.rs` source of truth — see [[mirror-keeper-role]] in the DOC-AF-004 response).
- Federation cut acknowledgements (pinning the docs surface to specific engine versions: currently v0.8.1).

## What this session doesn't claim

- **Engine builds.** `cargo build` against `~/code/arcflow-core` is the arcflow-core build-owner's job; this session never invokes it.
- **Engine source edits.** Per CLAUDE.md RULE 2, no Rust source in this repo.
- **Schema source of truth.** The engine's `schema.rs` is canonical; this session only updates the `.ts` mirror per [[schema-sync-rule-3]] and per the closure-rule discipline described in DOC-AF-004.

## Cadence

This session runs in `/loop` dynamic mode — 30-minute heartbeat between federation inbox sweeps. Each sweep:
- Reads new inbound federation messages from peers.
- ACKs / resolves / federates as appropriate.
- Applies any docs edits the inbound traffic implies.
- Re-runs linters when scripts or generated MDX are touched.

## Stale-row policy

Per the proposal, if no commit carries this session's ID for 30 minutes, the next session reading this registry can mark the row `inactive`. This session is responsible for marking itself `completed` at end-of-life rather than abandoning the row.

## Membership cross-reference

See `federation-membership.md` for `arcflow-docs`'s declaration of federation peer status (active with arcflow-core, project-merlin, oz-platform; reachable-but-quiet with chetak per CHK's v0.7.2 pin).
