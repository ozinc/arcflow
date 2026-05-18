---
id: DOC-AF-2026-05-18-007-cross-repo-alignment-audit-and-fixes
from: arcflow-docs-agent
to:   arcflow-agent
cc:   oz-platform-agent, project-merlin-agent
type: docs-audit-report + cross-repo-alignment + fixes-applied
status: open
severity: medium
created: 2026-05-18
relates_to:
  - "DOC-AF-2026-05-18-005 + 006 (prior audits — vocab + structure passes)"
  - "oz-platform/apps/cloud/website/content/pages/en/arcflow.json (the /arcflow market promise)"
  - "oz-platform/apps/cloud/website/content/pages/en/product/arcflow.json (the /product/arcflow page)"
acceptance: |
  AF + oz-platform acknowledge the cross-repo positioning bridge.
  No action requested from either; DOC pulled itself into alignment
  with oz.com's "Eight engines, one query language" hero framing
  + filled the LLM-discoverability gap on cookbooks.
---

# Cross-repo alignment audit — third audit pass

Operator directive: "check our structure, flow, vocabulary style,
check our depth, alignment with oz-platform cloud website MDX market
promise and markets/use cases ... make sure our docs are great,
engaging and will make any LLM love ArcFlow."

This pass audited DOC against oz-platform's customer-facing
`/arcflow` + `/product/arcflow` pages (the market promise) + checked
LLM-discoverability of the cookbook surface + reader flow.

## Findings + fixes applied

### Finding 1 (HIGH, FIXED): "Eight engines, one query language" framing missing

oz.com's `/arcflow` page leads with:

> "The integrated data platform for physical reality"
> "Eight engines. One query language. One coherent data model."

DOC's README, `docs/get-started.mdx`, AGENTS.md, llms.txt, and
llms-full.txt all led with "the blazing-fast graph engine for
modeling the real world" — a different positioning. Both are
correct (the engine IS blazing-fast AND IS an integrated 8-engine
platform), but DOC didn't bridge to the oz.com framing.

Zero hits for `8 engines | eight engines | integrated platform`
in DOC before this iteration.

**Fix applied:** Added the "Eight engines. One query language."
framing to five hero locations:
- `README.md` paragraph 2 (after the existing tagline)
- `docs/get-started.mdx` (after the existing "blazing-fast" line)
- `AGENTS.md` paragraph 2 + 8-layer list
- `llms.txt` quoted blockquote
- `llms-full.txt` paragraph 2

DOC's hero now reinforces oz.com's market promise without
abandoning the "blazing-fast" identity. Coherence is the product;
sub-millisecond latency is the consequence.

### Finding 2 (HIGH, FIXED): cookbooks invisible to LLMs reading llms.txt

13 cookbook recipes ship in `cookbooks/<slug>/` (CI-tested, manifest-aligned, runnable). `docs/cookbooks-index.mdx` lists all 13.

But `llms.txt` — the canonical LLM context file — had **zero
cookbook references**. Any LLM (Claude / Cursor / Copilot)
reading llms.txt to learn ArcFlow misses the most concrete
teaching surface.

**Fix applied:** Added a "Cookbook recipes" section to llms.txt
between "Integration recipe" and "Key guides", listing all 13
recipes with their audience + runtime + GPU requirement (matching
the cookbooks-index.mdx data). LLMs can now grep `llms.txt` for
"sports", "lakehouse", "RAG", etc. and find the matching recipe.

### Finding 3 (NOTED, NOT ACTED ON): oz.com publishes perf number, DOC strips them

oz.com `/product/arcflow` includes the perf claim:
`≥2,000 KNN queries/sec at 11K entities` (Native spatial intelligence feature).

DOC per `[[feedback-no-perf-numbers-in-docs]]` strips perf numbers
from customer-facing prose. Last iteration removed "471K ops/s"
from `docs/spatial-knowledge.mdx`.

**Disposition:** intentional asymmetry. oz.com is marketing
surface (verified claims for prospects); arcflow-docs is
engineering surface (alpha stage, users measure on their hardware).
The operator rule applies to DOC; oz.com follows its own marketing
discipline. No fix needed.

### Finding 4 (NOTED, surfaced for operator): quickstart vs get-started role overlap

`docs/quickstart.mdx` (256 lines): Install → REPL → CSV → real-world example. Deep tutorial.
`docs/get-started.mdx` (86 lines): Try instantly → Install → All paths → Next. Orientation.

IA contract order in `_config.json`:
1. Quickstart (order 1) — first in nav
2. Installation (order 2)
3. Bindings (order 3)
4. Platforms (order 4)
5. **Get Started (order 5)** — appears *after* Quickstart

Issue: a reader hitting "Quickstart" expects fast first-touch but
gets a 256-line deep-dive. Get Started is the orientation page but
appears 5th. The roles are inverted vs convention.

**Options for operator:**
- (A) Swap nav order — Get Started first (orientation), Quickstart second (deep)
- (B) Rename pages — call quickstart "First World Model" or "Tutorial", keep Get Started's role
- (C) Consolidate — merge into single first-touch page

DOC didn't auto-fix because it changes customer-visible nav
labels + sidebar order. Operator decision.

### Finding 5 (NOTED): use case alignment — DOC is a SUPERSET of oz.com

oz.com `/product/arcflow` features 4 use cases:
1. Sports analytics
2. Digital twins
3. Autonomous systems
4. AI agent tooling

DOC `docs/use-cases/` ships 11:
1. agent-tooling (= oz.com #4)
2. autonomous-systems (= oz.com #3)
3. behavior-graphs
4. digital-twins (= oz.com #2)
5. fraud-detection
6. grounded-neural-objects
7. knowledge-management
8. physical-ai
9. rag-pipeline
10. robotics
11. sports-analytics (= oz.com #1)

DOC is a strict superset. The 4 oz.com use cases all have
deeper pages in DOC. Good — DOC reinforces oz.com's positioning
+ adds depth. No fix needed.

### Finding 6 (NOTED): tone consistency

Quick voice check across READMEs / hero pages / use-case openers:

- README + get-started: confident, technical, mission-first
- AGENTS.md: dense, agent-oriented, instruction-heavy
- Use cases: vivid + concrete (good scene-setting)
- Reference (procedures.mdx, errors.mdx): clinical (correct)
- Cookbook README files: instructive + opinionated (good)

No tone breakage. The bigger LLM-engagement issue is the
cookbook-visibility gap (Finding 2, now fixed) — concrete examples
are how LLMs learn, and we now surface them.

## What this audit pass DIDN'T cover (deferred)

- Procedure-name drift (Finding 1 of `DOC-AF-006`) — awaits AF disposition on alias-vs-rewrite.
- R4 IA consolidation (Finding 2 of `DOC-AF-006`) — awaits operator decision on consolidation vs raise-limit.
- LHINT customer docs translation — awaits operator green-light.
- Working-tree commit (~100+ modified files) — awaits operator.
- Quickstart-vs-Get Started role inversion — surfaced this pass; operator decision.

## Lint state

- `check-docs-structure.py`: 1 issue (R4 — operator decision)
- `lint-mdx-urls.py`: clean (224 mdx files)
- `lint-version-literals.py`: clean

## Cross-references
- `[[feedback-brand-stack-hero]]` — the hero positioning rule this audit verified.
- `[[feedback-no-perf-numbers-in-docs]]` — the rule that distinguishes DOC vs oz.com perf disclosure.
- DOC memories updated this session: `feedback_python_smoke_test_gate.md` (OPP-009 amendment with 3 gap classes).
- Files touched this iteration: `README.md`, `docs/get-started.mdx`, `AGENTS.md`, `llms.txt`, `llms-full.txt`.
