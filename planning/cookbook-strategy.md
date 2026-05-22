# Cookbook Strategy (docs slice of arcflow I-INIT-0117)

This document records the **documentation-domain slice** of the cross-repo
initiative `I-INIT-0117 — Cookbook Strategy: Agent-Native, Manifest-Aligned Examples`
authored in the engine repo at
`arcflow/kanban/roadmap/initiatives/I-INIT-0117-Cookbook-Strategy.md`.

The full plan — including engine-side manifest cross-probes — lives in arcflow.
This file tracks the slice owned by this repo and the contract this repo has
with the manifest and the governing pattern PAT-0044 (Cookbook Recipe Governance).

External inspiration: [`cursor/cookbook`](https://github.com/cursor/cookbook) —
public, MIT, recipe-driven, agent-friendly examples repo. ArcFlow's cookbook
mirrors the content shape and adds a stronger manifest-alignment contract,
because the engine and the cookbook are versioned independently.

---

## NOTE(invariant): Recipes use only `status: shipped` APIs.

This invariant compounds with the existing one from `sdk-surface-docs.md`:

> Write docs for what exists. Never describe unimplemented APIs.

The manifest is the operational definition of "what exists." A recipe whose
`meta.toml.arcflow_apis` references an API the manifest reports as `planned`
or absent is a CI failure. There is no "this will work soon" recipe.

If a recipe needs a feature that has not shipped, the path is: ship the
feature in the engine repo, flip the manifest, then write the recipe.

---

## Why This Repo Hosts the Cookbook

Three bounded contexts, one shared kernel.

| Bounded context | Repo | Role |
|---|---|---|
| Engine domain | `arcflow/` (closed) | Authors PAT-0044, owns the manifest, runs the cross-probe |
| Documentation domain | `arcflow-docs/` (this repo, public MIT) | Hosts `examples/`, runs recipe CI, owns recipe authoring |
| Marketing/web domain | `oz-platform/apps/cloud/website/` | Auto-generated cookbook index page; deep-links to source |

This repo is the cookbook's home because:

- It is public MIT — recipes need to be MIT for customers and agents to copy
  freely.
- Cookbook recipes are *content*, which is this repo's domain (per `REPO-SPLIT.md`).
- This repo already houses the SDK source and developer-facing examples; the
  cookbook joins them as a peer surface.

This repo does **not** author the manifest, define what counts as `shipped`, or
adjudicate which APIs are eligible for cookbook coverage. Those decisions live
in the engine domain.

---

## What This Repo Owns (Post I-INIT-0117 Landing)

| Surface | Description |
|---|---|
| `examples/` (new) | Root of all recipes |
| `examples/README.md` | Index of recipes, audience tags, runtime estimates |
| `examples/_template/` | Copy-paste recipe skeleton |
| `examples/CONTRIBUTING.md` | Authoring rules from PAT-0044 |
| `examples/<slug>/` | Individual recipe directory per PAT-0044 layout |
| `examples/_demos/` | Recipes that cannot meet the CI runtime contract (GPU-required, sensor-stream-required, etc.) |
| `examples/_archive/<engine-version>/` | Recipes archived when their target engine major is no longer supported |
| `docs/cookbooks-index.mdx` | Auto-generated MDX index that the marketing site links to |
| `pnpm cookbook:test` | Recipe CI runner |
| `scripts/validate-meta-toml.ts` | Schema validator for recipe `meta.toml` |

---

## What This Repo Does NOT Own

- The manifest (`RELEASE-MATRIX.toml`) — engine domain.
- Cookbook governance rules — authored as PAT-0044 in
  `arcflow/kanban/patterns/`.
- Recipe authoring decisions for engine-internal capabilities the engine
  team has not yet promoted to public APIs — those are gate-locked at the
  manifest, not at this repo.
- The marketing-site cookbook landing page (`oz-platform/.../arcflow/examples/`)
  — owned by the marketing repo, but it auto-generates from this repo's
  `examples/*/meta.toml`, so changes here propagate there without a
  marketing-side PR.

---

## Recipe Layout (PAT-0044)

Every recipe under `examples/<slug>/` has:

```
examples/<slug>/
├── README.md               # ≤ 200 words: "what you'll build" + run command
├── 01-<step>.{md,py,ts}    # numbered, ordered steps
├── 02-<step>.{md,py,ts}
├── ...
├── data/                   # ≤ 5 MB sample data, in-tree, no external download
├── pyproject.toml OR package.json    # uv/pip/npm-installable, pins arcflow version
└── meta.toml               # recipe metadata
```

`meta.toml` declares which manifest APIs the recipe uses and which engine
version it pins to. CI cross-checks both.

See PAT-0044 in arcflow for the authoritative governance rules.

---

## Seed Recipe — Already Specified

The first recipe is delivered in I-INIT-0116 wave RAM-A4:
`examples/temporal-spatial-parquet-ingest/`. It is the customer-unblock
recipe for the football-transformer NGS use case (12 Parquet files, NFL
player tracking, temporal + spatial). It also seeds the structural template
that all subsequent recipes follow.

I-INIT-0117 finalizes the surrounding governance, the `_template/`, the CI
runner, and ships three more recipes (sensor fusion, fraud graph, agent
knowledge base) to validate the structure under load.

---

## Cookbook CI Runner — Operational Contract

`pnpm cookbook:test` in this repo:

1. Walks `examples/<slug>/` and skips `_template/`, `_demos/`, `_archive/`.
2. For each recipe:
   - Validates `meta.toml` against the schema.
   - Fetches `release-matrix.json` (engine-published; pinned to
     `meta.toml.manifest_pin`).
   - Asserts every API in `meta.toml.arcflow_apis` resolves to `status: shipped`.
   - Installs deps via `uv sync` or `pnpm install` based on recipe language.
   - Runs each numbered step in order to completion in ≤ `runtime_minutes`.
   - Snapshots the terminal step's deterministic output and asserts byte-equal
     against the committed snapshot.
3. Fails closed on any error. No retries, no warn-only mode.

When the engine repo's release CI runs the cross-probe (I-INIT-0117 CB-0003),
it reads `examples/*/meta.toml` from this repo as data. There is no
cooperative protocol; the probe is one-way. This repo is a pure read target
for the engine's release gate.

---

## CI Lint Rule (Beyond PAT-0044)

After CB-0001:

```text
required in examples/<slug>/:
  meta.toml             must exist and validate
  README.md             must exist and be ≤ 200 words for "what you'll build"
  pyproject.toml OR package.json   must declare arcflow as a dep
  01-*.{md,py,ts}       must exist (at least one numbered step)

forbidden in examples/<slug>/:
  curl/wget downloads in any step (sample data must be in-tree)
  references to APIs absent from the manifest at meta.toml.manifest_pin
  hand-rolled `pip install arcflow` commands (use the `<InstallMatrix />` link)
```

---

## Relationship to Existing Repo Surfaces

- **`docs/`** — Reference docs. Multi-page narratives, MDX, hand-authored.
  Stays as is.
- **`docs/guides/`** — Multi-step tutorials that don't fit the recipe shape.
  Stays as is.
- **`examples/`** — Pre-existing examples directory (if any). Cookbook is
  the *governed* successor. Existing examples migrate into `examples/` per
  PAT-0044 or get deleted; greenfield rule applies — no parallel example
  trees.
- **`fixtures/`, `schemas/`** — Cookbook recipes may reference these but do
  not duplicate them.

---

## Cross-Repo Coordination

| Repo | What it does | Reads | Writes |
|---|---|---|---|
| arcflow (engine) | Author PAT-0044, run cross-probe in release CI | this repo's `examples/*/meta.toml` | nothing in this repo |
| arcflow-docs (this repo) | Author recipes, run recipe CI | engine's `release-matrix.json` | `examples/` |
| oz-platform (web) | Surface auto-generated index | this repo's `examples/*/meta.toml` | nothing in this repo |

One-way reads only. No cooperative protocol between repos. Manifest is the
shared kernel; recipes are the consumed artifact downstream.

---

## Resume Point for the Customer

The customer (football-transformer NGS world model) is unblocked by
I-INIT-0116 wave RAM-A4 — the seed recipe `temporal-spatial-parquet-ingest`
ships alongside the Python wheel. The broader cookbook structure (this
initiative) makes that recipe the first of many.

Subsequent customers with the same shape (large temporal + spatial Parquet
batches) follow the same recipe; subsequent customers with different shapes
(sensor fusion, fraud graphs, agent KB) follow CB-0004 recipes.
