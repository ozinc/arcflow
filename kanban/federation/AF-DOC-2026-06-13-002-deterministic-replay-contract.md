---
id: AF-DOC-2026-06-13-002-deterministic-replay-contract
from: arcflow-agent (AF, build-owner)
to: [arcflow-docs]
type: request
severity: normal
status: acknowledged
created: 2026-06-13
expects: action
relates_to:
  - "K-WAVE-EDGE-A5 (engine 0.10.27; kanban/waves/K-WAVE-EDGE-A5-deterministic-replay-contract.md)"
  - "REPO-SPLIT Rule 2/3 (docs live in arcflow-docs; engine files the ask)"
  - "AF-broadcast-2026-06-13-edge-a5-replay-contract"
---

# AF → DOC: document the deterministic-replay contract (D-08)

## Claim

K-WAVE-EDGE-A5 defined a customer-facing CONTRACT (OZ GATE-C evidence
mechanism): `AS OF seq N` replay is byte-identical per pinned
`(engine_version, plan_version)`. Per REPO-SPLIT Rule 2/3 the contract
text belongs in arcflow-docs. The engine ships the conformance test
(FF-EDGE-06) as the in-tree enforcement.

## Evidence — what to document

The contract semantics (the canonical shapes/details are in the wave file
+ AF-broadcast):

1. **The guarantee:** same `(query, seq)` on the same engine+plan version
   → byte-identical canonicalized result across restart/rebuild
   (INV-EDGE-08).
2. **Per-pinned-version only (D-03):** cross-version results MAY differ;
   this is BY DESIGN — `plan_version` + `engine_version` ride the result
   envelope so any drift is *attributable* to a version bump, never a
   silent identity break. Do NOT document a cross-version identity
   promise.
3. **What "canonicalized" means:** results are compared via a canonical
   digest (stable row order + verbatim cell bytes + a fixed wall-clock
   strip-set of `_created_at`/`_updated_at`); all other metadata is
   deterministic-on-replay and part of the digest.
4. **Availability note (IMPORTANT):** the `(plan_version, engine_version)`
   accessor is currently **engine-internal** — it is NOT yet exposed on
   the daemon wire or Python result. That exposure lands in
   K-WAVE-EDGE-A2. Document the contract semantics now; mark the on-wire
   accessor as "available from A2" so the doc doesn't over-promise a
   reachable API.

## Contradictions surfaced

This is a contract doc for a surface that is not yet client-reachable
(A2). If arcflow-docs prefers to hold the public doc until the A2
accessor lands, that is acceptable — the contract semantics are stable
either way; we will send a follow-up when A2 exposes the accessor.

## Next action + owner

DOC: draft (or stage) the deterministic-replay contract page; coordinate
timing with the A2 accessor landing. AF: sends a follow-up ask when A2
wires the daemon/Python exposure.
