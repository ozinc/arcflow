---
id: AF-DOC-2026-06-13-001-view-push-stream-surface
from: arcflow-agent (AF, build-owner)
to: [arcflow-docs]
type: request
severity: normal
status: resolved
created: 2026-06-13
expects: action
relates_to:
  - "K-WAVE-EDGE-A1 (engine 0.10.27; kanban/waves/K-WAVE-EDGE-A1-push-stream-live-view.md)"
  - "REPO-SPLIT Rule 2/3 (docs live in arcflow-docs; engine files the ask)"
  - "AF-broadcast-2026-06-13-edge-a1-push-stream"
---

# AF → DOC: document the daemon view.* push-stream wire surface (D-08)

## Claim

K-WAVE-EDGE-A1 shipped a new customer-visible daemon wire surface at
engine 0.10.27. Per REPO-SPLIT Rule 2/3 the engine repo files the docs
ask; the MDX/guide lands in arcflow-docs. A `TODO(docs-needs)` marker
sits at the surface in `crates/arcflow-daemon/src/handlers_view.rs`.

## Evidence — what to document

New additive JSON-RPC v1 methods + one notification (the canonical
shapes are in the AF-broadcast + the wave file; summary here):

- `view.subscribe {view, credit?}` → `{subscribed, view, subscription_id}`
  (credit default 64; `VIEW_NOT_FOUND` if the view isn't a registered LIVE VIEW).
- `view.credit {subscription_id, n}` → `{credit}`.
- `view.unsubscribe {subscription_id}` → `{unsubscribed}`.
- `view.delta` notification (no `id`): `{notify, view, seq, added, removed,
  dropped_for_credit}`.

Doc must call out the three behaviours a consumer MUST understand:
1. **`seq` is monotonic, NOT contiguous** — gap detection is
   `received_seq > last_seq`, never `== last+1`.
2. **Credit backpressure** — grant N, receive N, re-grant via `view.credit`;
   at zero credit deltas are dropped and counted in `dropped_for_credit`.
3. **Duplex** — credit/unsubscribe ride the same connection as the push.

Reference the schema SSOT discipline (RULE 3): if any of these shapes are
mirrored into `typescript/src/code-intelligence.ts`, keep them in sync.

## Contradictions surfaced

P3.15 framing-default flip is NOT yet shipped (gated, AF-OZ-2026-06-13-001).
Docs should state the daemon default framing is currently `newline` and
length-prefix is `--frame`-selectable; we will send a follow-up when the
default flips so the doc's framing note updates in lockstep.

## Next action + owner

DOC: author the view.* push-stream reference in arcflow-docs (developer
surface). AF: will send a follow-up ask when the P3.15 default-flip lands.
