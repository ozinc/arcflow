# ArcFlow Cookbook

Runnable, manifest-aligned reference implementations of ArcFlow capabilities.

Every recipe here is a self-contained, end-to-end working example. CI runs each
recipe on every commit. Recipes use only ArcFlow APIs whose status in
[`release-matrix.json`](https://pub-a0a196dbe10340f8af22524547fdd476.r2.dev/releases/arcflow/release-matrix.json)
is `shipped`.

Inspired by [`cursor/cookbook`](https://github.com/cursor/cookbook), with a
stronger contract — every recipe is CI-tested against the engine version it
pins to. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the operating rules.

## Recipes

| Recipe | Audience | Runtime | Engine version |
|---|---|---|---|
| [agent-knowledge-base](./agent-knowledge-base/) | python, agent | ~5 min | 1.6.6 |
| [fraud-graph-traversal](./fraud-graph-traversal/) | python, data-engineer | ~5 min | 1.6.6 |
| [multi-stream-spatiotemporal-world-model](./multi-stream-spatiotemporal-world-model/) | python, data-engineer, ml, agent | ~8 min | 1.6.6 |
| [sensor-fusion-livequery](./sensor-fusion-livequery/) | python, ml | ~5 min | 1.6.6 |
| [temporal-spatial-parquet-ingest](./temporal-spatial-parquet-ingest/) | python, data-engineer | ~5 min | 1.6.6 |

## Run a recipe

```bash
cd cookbooks/<recipe-slug>
uv sync                       # installs deps, including arcflow
uv run python 01-*.py         # run each numbered step in order
```

ArcFlow installation comes from [the install matrix](https://oz.com/docs/installation).
The Python wheel resolves through OZ's PEP 503 simple index at
`https://staging.oz.com/pypi/simple/` (configured in each recipe's `pyproject.toml`).

## Folder layout

- `<recipe-slug>/` — one runnable recipe
- `_template/` — copy-paste skeleton for new recipes
- `_demos/` — recipes that can't meet the CI runtime contract (GPU-required,
  sensor-stream-required, etc.). Manual reproduction; not in the main index.
- `_archive/<engine-version>/` — recipes archived when their target engine
  major is no longer supported.

## Governance summary

- One recipe = one runnable end-to-end example.
- Recipes use only `status: shipped` ArcFlow APIs.
- Sample data ≤ 5 MB, in-tree, no external download.
- CI runs every recipe end-to-end on every commit. Fail closed.

Full rules in [`CONTRIBUTING.md`](./CONTRIBUTING.md).
