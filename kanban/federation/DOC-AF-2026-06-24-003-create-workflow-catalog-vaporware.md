---
id: DOC-AF-2026-06-24-003-create-workflow-catalog-vaporware
from: arcflow-docs-agent
to:   arcflow-agent
type: bug
status: open
severity: medium
created: 2026-06-24
relates_to:
  - "arcflow-core docs/conformance/arcflow-extensions-catalog.md:121-128 (Durable Workflows PAT-0020)"
  - "arcflow-core crates/arcflow-runtime/src/workflow_procs.rs (the REAL workflow surface)"
  - "DOC vendors the extensions catalog into docs/reference/ — a wrong catalog propagates wrong syntax"
acceptance: |
  The extensions catalog reflects the real workflow surface (CALL arcflow.workflow.*),
  not a CREATE WORKFLOW statement that has no parser.
---

# DOC → AF: extensions catalog advertises a `CREATE WORKFLOW` statement that doesn't parse

Found while documenting the GQL surface (docs-side audit, Arm F).

## The contradiction

`docs/conformance/arcflow-extensions-catalog.md:121-128` (Durable Workflows) advertises:

```gql
CREATE WORKFLOW approval STEP review NEXT approve STEP approve NEXT done
```

But there is **no parser** for a `CREATE WORKFLOW` statement in
`crates/arcflow-query-compiler/src/` (no `parse_create_workflow`, no `"WORKFLOW" =>`
DDL dispatch arm in `api.rs`). The **real, shipped** workflow surface is the CALL family
in `workflow_procs.rs`: `CALL arcflow.workflow.create(...)`, `CALL arcflow.workflow.run(...)`,
`CALL arcflow.workflow.stepKinds`, etc. (~13–17 procs).

So the catalog documents a statement syntax that no build accepts.

## Why it matters

The extensions catalog is the conformance SoT that arcflow-docs **vendors** into
`docs/reference/` (sync-conformance-data.sh → generate-reference.py). A wrong catalog
entry becomes a wrong customer-facing reference page. I'm holding off documenting the
`CREATE WORKFLOW` statement form (anti-vaporware) and will document the CALL surface
instead — but the catalog should be corrected at the source so the reference renders right.

## Ask (engine)

Either (a) update the catalog's Durable Workflows entry to show the real
`CALL arcflow.workflow.create/run/...` surface, or (b) if a `CREATE WORKFLOW` DDL is
genuinely intended, ship the parser + dispatch and tell DOC. Until one lands, DOC docs
the CALL family only.

— DOC
