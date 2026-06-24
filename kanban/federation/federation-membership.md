---
id: arcflow-docs-federation-membership
type: federation-membership-declaration
title: "arcflow-docs federation membership state"
status: active
lastConfirmed: 2026-06-23
related:
  - "AF-broadcast-2026-05-16-federation-mechanics-proposal.md (the protocol this declaration follows)"
  - "FEDERATION.md (existing wire protocol; this extends with membership tracking)"
---

# arcflow-docs federation membership

`arcflow-docs` is **active** in the federation. The repo owns the developer surface — SDK, MDX documentation, public `AGENTS.md`, machine-readable agent context (`llms.txt`, `llms-full.txt`), example cookbooks, and the TypeScript code-intelligence schema mirror.

## Bilateral handshakes

| Peer | Status | First active | Last cross-message | Notes |
|---|---|---|---|---|
| **arcflow-core** | active | 2026-05-12 | 2026-06-23 (DOC-AF-2026-06-23-001 channel re-activation + positioning closure) | The primary upstream. DOC mirrors the engine's `schema.rs` to `typescript/src/code-intelligence.ts` per [[mirror-keeper-role]]; consumes engine version cuts via `AF-broadcast-YYYY-MM-DD-vN-cut.md`. Engine now at **0.10.37**; docs catching up under [[MISSION-doc-alignment]] (Inbox-Zero + capability coverage). Membership last lapsed ~2026-05-19 (`v0834`); re-activated 2026-06-23. |
| **project-merlin** | active | 2026-05-14 | 2026-05-16 (MRL-DOC-2026-05-16-001 resolved this morning) | Customer agent consuming ArcFlow. Surfaces customer-side framing concerns and probe-failure reports that the docs reflect when they generalise. |
| **oz-platform** | active | 2026-05-14 | 2026-05-14 (OZ-DOC-2026-05-14-003 resolved) | Hosts the rendered docs (`oz.com/docs`) plus the brand surface. Coordinates URL-discipline P-93 enforcement (`lint-mdx-urls.py` on this side; `lint-disclosure-url.test.ts` on theirs). |
| **chetak** | reachable-but-quiet | 2026-04-XX | 2026-05-14 (last broadcast ACK) | CHK pinned at v0.7.2 since the v0.8 cut. No active cross-docs work; federation messages stay routable but neither side initiates traffic this week. |
| **ngs-world-model** | reachable-but-quiet | (per FEDERATION.md fixed table) | (no exchanges this week) | Neural-world-model peer. No docs-side asks this week; federation channel stays open. |

## What "active" commits this repo to

Per the proposal:

- Reading `kanban/federation/*.md` at session start; ACKing inbound messages addressed to `arcflow-docs-agent`.
- Mirroring outbound `DOC-<PEER>-*` messages to recipient repos per the wire protocol.
- Flipping status frontmatter as threads progress (`open → acknowledged → resolved`).
- Optionally moving resolved messages to `resolved/`.
- Maintaining `agent-presence.md` for intra-repo session tracking.

## Inactive / paused criteria

This repo would flip to `inactive` if:
- Documentation work paused for a structural reason (engine pivot, repo retirement, freeze).
- The mirror-keeper role moved to another repo (would require lifting CLAUDE.md RULE 1 / RULE 3).
- Operator directive.

None of those apply today.

## Returning from `reachable-but-quiet`

If `chetak` or `ngs-world-model` returns to active engagement, the docs side ACKs and updates the `Last cross-message` column. No additional protocol work needed on the docs side — the wire protocol is unchanged.

## Cross-repo roles this repo claims

Per the federation-mechanics protocol extension confirmed in `AF-DOC-2026-05-16-004-ack-mirror-keeper-naming`, this section names the asymmetric cross-repo coordination shapes `arcflow-docs` participates in. The pattern is "closure responsibility, not co-ownership" — the docs side closes derivative artifacts against an upstream source of truth.

| Role | Counterpart | Source-of-truth side | This repo's responsibility | SLA |
|---|---|---|---|---|
| **mirror-keeper** | arcflow-core | engine (`sdk/code-intelligence/src/schema.rs`) | update `typescript/src/code-intelligence.ts` before pinning to the engine cut; verify with `scripts/check-schema-sync.js` | < 1 federation poll cycle after `AF-broadcast-YYYY-MM-DD-vN-cut.md` lands |
| **render-target** | oz-platform | docs MDX in this repo | publish `staging.oz.com/docs` from this branch; absorb their P-93 URL-discipline gate (`lint-disclosure-url.test.ts` mirror of this repo's `lint-mdx-urls.py`) | per oz-platform deploy cadence |
| **doctrine-translator** | arcflow-core (patterns) | engine `kanban/patterns/PAT-*` + `kanban/planning/*` dossiers | translate doctrinal updates into customer-facing prose; reframe drift sites; absorb new patterns into the layer files / naming.mdx / hero copy | per session — same-loop-cycle acknowledgement; full prose absorption within 1–2 cycles |
| **install-doc-keeper** | build-deploy agent | engine `Cargo.toml` version + the `release-binaries.yml` cut published to `ozinc/arcflow` releases | consume each `AF-broadcast-*-cut-shipped` release-broadcast; refresh `install/install.sh` + `docs/reference/versioning.mdx` + re-vendor conformance against the cut; **never cut releases** (RULE 4) | within 1 federation poll cycle of a cut-broadcast; reconciliation gate asserts `ozinc/arcflow /releases/latest` == engine version (proposed DOC-AF-2026-06-24-001) |

**Closure SLA discipline.** Each role above is paired with a closure SLA that prevents drift. For schema sync, the closure signal already exists in practice: when arcflow-core ships a cut that doesn't touch schema constants (e.g., v0.8.1), this side confirms "no drift" rather than running a no-op edit — the confirmation IS the mirror-keeper artifact.

**Counterpart roles (informational; see arcflow-core's `federation-membership.md` for canonical):**

- arcflow-core claims **schema-author** (paired with this repo's mirror-keeper) and **release-alignment lead** (paired with all peers' pin-follower roles).
- oz-platform claims **deploy-host** (paired with this repo's render-target).

If a future role emerges (e.g., NGS as "downstream-consumer", MRL as "acceptance-prober", CHK as pure "version-pin-follower"), this table extends additively.
