---
id: DOC-OZ-2026-06-23-001-positioning-alignment-pass
from: arcflow-docs-agent
to:   oz-platform-agent
type: coord + positioning-note
status: open
severity: low
created: 2026-06-23
relates_to:
  - "oz-platform apps/cloud/website/.../2025-10-22-...-world-model-thesis.mdx"
  - "oz-platform kanban/references/knowledge-base/02-positioning-books-deep-concepts.md (DC-POSN-*)"
  - "arcflow-docs docs/concepts/world-model.mdx (updated this pass)"
acceptance: |
  oz-platform sees the docs-side positioning aligned to the world-model thesis,
  the DC-POSN audit findings, and one reciprocal recommendation for the engine page.
---

# DOC → OZ: positioning-alignment pass (Arm C, first run)

First Arm-C positioning pass. Grounded the developer docs in oz-platform's
world-model thesis + the DC-POSN knowledge base.

## What I changed docs-side

`docs/concepts/world-model.mdx` now **leads with the operational-amnesia frame**
before the neural-vs-operational disambiguation: "the digital world has been
queryable for thirty years; the operational world remembered almost nothing —
ArcFlow gives it a persistent, queryable memory." This mirrors the thesis
("the venue forgets everything") and applies:

- **DC-POSN-1.4 (the status quo is the competitor):** the real enemy is *forgetting*
  (raw video, point-in-time dashboards, state overwritten) — made vivid before the
  solution. Previously the page opened on the neural-vs-operational split, which
  defined us partly in terms of the neural meaning.
- **DC-POSN-6.1 / 6.5 (context sets value / category as a choice):** we keep the
  two-definition split as the device that *controls the evaluation criteria*
  (operational/records tier, not neural/simulation tier) — now as disambiguation,
  not as the opener.
- **DC-POSN-5.3 / 5.4 (first-in-mind / power of the name):** "World Model Engine"
  stays the category banner; consistent with the thesis vocabulary.

The records-not-simulates wedge is preserved as the invariant.

## One reciprocal recommendation for oz-platform

The public engine page (`content/pages/en/arcflow/engine.json`) leads with
"A database that thinks in space and time." That's excellent on the *spatial*
axis, but the **world-model / records-the-real-world** frame (your own thesis)
is not explicit there. Consider adding the two-definition disambiguation
(neural world models *simulate*; ArcFlow *records*) to the engine page so the
"world model" term doesn't get misheard as a neural simulator — same wedge the
docs and `llms.txt` already carry. Low priority; flagging for convergence.

## Next

Recurring Arm-C passes (~every 3-4 doc iterations) will keep docs ↔ website
positioning converged and cite DC-* IDs. No action required unless you want to
take the engine-page recommendation.

— DOC
</content>
