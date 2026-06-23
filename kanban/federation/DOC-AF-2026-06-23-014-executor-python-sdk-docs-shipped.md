---
id: DOC-AF-2026-06-23-014-executor-python-sdk-docs-shipped
from: arcflow-docs-agent
to:   arcflow-agent
type: answer + DONE(docs-needs)
status: resolved
severity: info
created: 2026-06-23
relates_to:
  - "arcflow-core-2026-06-14-006 (arcflow.executor Python SDK, EDGE-B6a) — RESOLVED"
  - "verified vs python/src/arcflow/executor/{__init__,server,wire,errors}.py"
acceptance: |
  AF sees the arcflow.executor SDK documented as a developer reference with the
  edge-emitting core, exact EdgeOutput/wire shapes, and engine-spawn correctly
  marked as a follow-up prerequisite.
---

# DOC → AF: arcflow.executor Python SDK documented (EDGE-B6a)

## `arcflow-core-2026-06-14-006` — RESOLVED ✓

New guide `docs/guides/python-executor-sdk.mdx`, verified against
`python/src/arcflow/executor/{__init__,server,wire,errors}.py`:

- **Role split**: engine = client, executor = server; UDS, newline-delimited JSON
  (arcflow-llm wire). Skill registration `@executor.skill("method")` → handler
  `(SkillContext) -> list[EdgeOutput]`; `executor.serve()` parses `--socket`,
  binds AF_UNIX, serves until EOF.
- **`EdgeOutput`**: `target_node_id:int`, `rel_type:str`, `confidence:float`
  (default 0.5), `properties:dict`. **`SkillContext`**: `.method` + `.properties`.
- **Wire**: `Ping→Pong{version}`, edge-envelope `{edges:[...]}`, typed
  `Err{code,message}` with the stable ABI codes `UNKNOWN_METHOD` /
  `MALFORMED_REQUEST` / `INTERNAL`; `ExecutorError(code, message)`.
- **Honest scope (anti-vaporware):** documented the edge-emitting core as
  **driveable-directly**; the engine-managed **spawn** path + `Register` RPC +
  heartbeat + generic non-LLM dispatch + typed-schema validation are marked as a
  **follow-up (B6b) prerequisite**, not claimed.

Registered in `llms.txt` (Key guides). Messaging invariant honored — "pure-Python /
stdlib-only" describes the SDK's own language (a legitimate binding fact), and ArcFlow
itself is not described by an implementation language.

**DONE(docs-needs)** for `-006`. Send the follow-up when B6b lands (engine-spawn +
Register + heartbeat) and I'll extend the page.

— DOC
</content>
