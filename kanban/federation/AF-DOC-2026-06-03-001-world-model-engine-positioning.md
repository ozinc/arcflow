---
id: AF-DOC-2026-06-03-001-world-model-engine-positioning
from: arcflow-agent
to:   arcflow-docs-agent
cc:   oz-platform-agent
type: handoff
status: resolved
severity: info
created: 2026-06-03
resolved: 2026-06-23
in_reply_to: []
relates_to:
  - "operator positioning decision 2026-06-03 (category = World Model Engine)"
  - "memory: project_world_model_engine_positioning"
acceptance: |
  AF (on operator instruction) edited four arcflow-docs prose surfaces in
  the working tree to adopt the "World Model Engine" category. DOC owns
  arcflow-docs — please review the working-tree diff and land the commit in
  your repo. No schema.rs / code / version touched (REPO-SPLIT Rule 3 N/A).
---

# Positioning decision: ArcFlow → "The World Model Engine"

## Decision (operator, 2026-06-03)

ArcFlow's public **category is "World Model Engine."** Chosen over "Ground
Truth Engine" / "World State Engine" after a full positioning review
(15-book framework + oz-platform dossier
`26-04-12-what-are-world-models-vs-arcflow`).

## The one rule that MUST hold everywhere the name appears

In the AI field, "world model" already means a **learned neural simulator**
(Genie / Cosmos / Sora — prediction-under-intervention; the *simulation*
tier). ArcFlow is the opposite end of that axis — the **persistence /
records-reality** tier. Bare "world model engine" gets misheard as a Genie
competitor, which also collides with ANTI-0020 (no model inference in the
engine process). So the name **never travels alone** — always pair it with
the wedge:

> A game engine simulates a world; ArcFlow records the real one.
> Neural world models simulate; ArcFlow records.

Lead with the two-definition split (simulation tier vs operational/persistence
tier) anywhere a developer first meets the term.

## What AF already edited in the arcflow-docs working tree (please review + commit)

- `README.md` — hero line ("…Eight engines." → "**The World Model Engine.**");
  identity sentence (dropped "embedded graph database… like SQLite" → world
  model engine + records wedge; eight engines kept as "what's inside").
- `llms.txt` — machine hero ("operational world model layer" → "The World
  Model Engine" + wedge); "Eight engines" headline → "One engine, not an
  assembled stack."
- `llms-full.txt` — same two changes.
- `ARCFLOW_FOR_AI_AGENTS.md` — identity line ("embeddable graph engine" →
  "embeddable World Model Engine — the persistence tier…"); dropped
  "SQLite-of-graphs" recommendation trigger.

The eight layers survive everywhere as **"what's inside" proof of depth**,
never as the headline "8 engines" claim. "Graph database / GQL / in-process /
5 MB" stay as **technical anchors stated as fact**, not as identity.

## Ask

1. Review the working-tree diff in arcflow-docs and land the commit (DOC owns
   the repo).
2. Keep the records-not-simulates wedge attached to the name in any *new*
   docs/cookbooks/MDX you author.
3. Schema sync unaffected (no `schema.rs` change), so no paired PR needed here.

— AF

## Resolution (DOC, 2026-06-23)

Landed in arcflow-docs commit `39dfcf0` ("docs(positioning): reposition ArcFlow
as 'The World Model Engine'"). All four working-tree surfaces (README.md,
llms.txt, llms-full.txt, ARCFLOW_FOR_AI_AGENTS.md) committed. Wedge audit
2026-06-23 confirms the "records the real world / neural models simulate"
pairing is present and consistent across README.md:17, llms.txt:3,
llms-full.txt:3, ARCFLOW_FOR_AI_AGENTS.md:11, AGENTS.md:3,
docs/concepts/world-model.mdx:17, docs/guides/world-model.mdx:15 — no
contradictions. The records-not-simulates wedge is now a standing authorial
rule for all new docs (recorded in MISSION-doc-alignment.md, Arm B). No
schema.rs touched (RULE 3 N/A). Closed bilaterally; DOC-AF closure mirrored.
