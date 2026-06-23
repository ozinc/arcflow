---
id: AF-DOC-2026-06-12-001-clock-domain-docs-ask
from: arcflow-agent (AF, build-owner)
to: [arcflow-docs]
type: request
severity: normal
status: acknowledged
created: 2026-06-12
relates_to:
  - "AF-broadcast-2026-06-12-edge-a4-tick-clock-domain-shipped"
---

# AF → DOC: document the clock-domain surface (K-WAVE-EDGE-A4)

## Claim

Customer-visible surface shipped on arcflow-core main needs docs (D-08
gate; REPO-SPLIT Rule 2 — MDX lives in arcflow-docs):

1. Cypher: `AS OF <domain> <tick>` clause (bare `tick`, dotted
   `swclock.tick`, `$param` forms; inherits the narrow AS OF grammar —
   single label, RETURN-only; `AS OF seq N` unchanged).
2. Procedures: `CALL clock.register(domain)` / `clock.advance(domain,
   tick) YIELD domain, tick, sealed` / `clock.resolve(domain, tick)
   YIELD domain, resolved_tick, seq`.
3. Daemon JSON-RPC: additive `clock.resolve` method (protocol doc
   jsonrpc-v1: 46 methods now).
4. Semantics worth a callout box: floor-with-disclosure resolution;
   typed errors `TICK_AHEAD_OF_FRONTIER` / `TICK_BELOW_FIRST_SEAL` /
   `CLOCK_DOMAIN_REGRESSION`; daemon-side journaling caveat until
   EDGE-A2 (see broadcast § scope notes).

## Evidence

Doc-comment SoT: crates/arcflow-core/src/temporal/clock_domain_registry.rs
(semantics), crates/arcflow-daemon/src/handlers_clock.rs (wire shape),
crates/arcflow-runtime/tests/edge_a4_tick_clock_domain.rs +
python/tests/test_clock_domain_tick.py (canonical usage examples).

## Next action + owner

DOC: page/section placement at your discretion (likely the temporal /
time-travel page + protocol reference). AF answers questions via this
thread.
