# ArcFlow Cookbook

Runnable, manifest-aligned reference implementations of ArcFlow capabilities.

Every recipe here is a self-contained, end-to-end working example. CI runs each
recipe on every commit. Recipes use only ArcFlow APIs whose status in
[`release-matrix.json`](https://pub-a0a196dbe10340f8af22524547fdd476.r2.dev/releases/arcflow/release-matrix.json)
is `shipped`.

Inspired by [`cursor/cookbook`](https://github.com/cursor/cookbook). Stronger
contract: see [`CONTRIBUTING.md`](./CONTRIBUTING.md) and the governance pattern
[PAT-0044 in the engine repo](../../arcflow/kanban/patterns/PAT-0044-Cookbook-Recipe-Governance.md).

## Recipes

| Recipe | Audience | Runtime | Engine version |
|---|---|---|---|
| [temporal-spatial-parquet-ingest](./temporal-spatial-parquet-ingest/) | python, data-engineer | ~5 min | 1.6.6 |

More recipes land in I-INIT-0117 wave CB-0004:
sensor-fusion-livequery, fraud-graph-traversal, agent-knowledge-base.

## Run a recipe

```bash
cd cookbooks/<recipe-slug>
uv sync                       # installs deps, including arcflow
uv run python 01-*.py         # run each numbered step in order
```

ArcFlow installation comes from
[the install matrix](https://oz.com/docs/installation). During alpha, recipes
pin to a hand-delivered local wheel via the recipe's `pyproject.toml`.

## Folder layout

- `<recipe-slug>/` — one runnable recipe (governed by PAT-0044)
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
