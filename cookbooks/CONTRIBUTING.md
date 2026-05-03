# Contributing to the ArcFlow Cookbook

This file is the operational summary for adding or updating a recipe.

## Folder layout (every recipe)

```
cookbooks/<slug>/
├── README.md               # ≤ 200 words: "what you'll build" + run command
├── 01-<step>.{md,py,ts}    # numbered, ordered steps
├── 02-<step>.{md,py,ts}
├── ...
├── data/                   # ≤ 5 MB sample data, in-tree, no external download
├── pyproject.toml OR package.json    # uv/pip/npm-installable
└── meta.toml               # recipe metadata (see below)
```

## meta.toml fields

```toml
slug = "your-recipe-slug"           # MUST match folder name
title = "Human-readable Title"
audience = ["python", "data-engineer"]   # any of: python, typescript,
                                         # data-engineer, ml, agent
arcflow_apis = [                    # APIs the recipe uses
    "python.ArcFlow.execute",
    "python.ArcFlow.close",
]
external_deps = ["pyarrow >= 16"]   # third-party libs the recipe expects
runtime_minutes = 5                 # CI cap; recipes >10 min go to _demos/
gpu_required = false                # GPU recipes go to _demos/
manifest_pin = "1.6.6"              # engine version this recipe targets
data_provenance = "synthesized"     # in {synthesized, anonymized, public}
```

## What recipes MAY do

- Demonstrate one ArcFlow capability per recipe. Compose only when the
  composition itself is the lesson.
- Use widely-available third-party libs (`pyarrow`, `duckdb`, `pandas`, `numpy`).
  No paid services, no API keys.
- Compare ArcFlow to a peer tool when the comparison is the lesson (factual,
  not marketing).
- Be agent-targeted. READMEs should be parseable by an LLM agent — terse,
  structural, no hidden context.

## What recipes MAY NOT do

- Describe a feature whose `release-matrix.json` `status` is `planned`. CI
  cross-checks `meta.toml.arcflow_apis` against the manifest.
- Skip CI by checking in expected outputs without re-running.
- Require external data downloads. Sample data is in-tree, ≤ 5 MB.
- Include real customer data (anonymized samples may approximate shape; they
  may not invent quantitative claims). `data_provenance` field is mandatory.
- Embed install commands hand-rolled. Install commands flow from the
  live `<InstallMatrix />` on the docs site, which is rendered from the
  release manifest.

## Adding a new recipe

```bash
cp -r cookbooks/_template cookbooks/<your-slug>
# ... fill in steps and meta.toml
# Run locally:
cd cookbooks/<your-slug>
uv sync
uv run python 01-*.py
# ... etc.
# Open PR. CI runs `pnpm cookbook:test` which executes every step.
```

## CI contract

`pnpm cookbook:test` walks every `cookbooks/<slug>/` (skipping `_template/`,
`_demos/`, `_archive/`) and:

1. Validates `meta.toml` against the schema.
2. Fetches `release-matrix.json` (pinned to `meta.toml.manifest_pin`).
3. Asserts every API in `meta.toml.arcflow_apis` resolves to `status: shipped`.
4. Installs deps via `uv sync` (or `pnpm install`).
5. Runs each numbered step in order to completion within `runtime_minutes`.
6. Snapshots the terminal step's deterministic output and asserts byte-equal
   against the committed snapshot.

CI fails closed on any error. No retries, no warn-only mode.

## Engine-side cross-probe

When the engine repo cuts a release, its CI runs `probe-cookbook-coverage` —
it scans every recipe's `meta.toml.arcflow_apis` and fails the engine release
if any API was removed or renamed without a recipe update. This closes the
loop: the engine cannot break a documented capability silently.

This means: if you add an API reference to a recipe, expect the engine team
to maintain that API. If they need to change it, they update the recipe in
the same PR. The recipe is part of the public contract.
