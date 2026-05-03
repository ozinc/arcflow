#!/usr/bin/env python3
"""Generate docs/cookbooks-index.mdx from cookbooks/*/meta.toml.

PAT-0044 invariant: the cookbook index is data-driven. The recipe list
on the index page is regenerated from each recipe's meta.toml, never
hand-edited.

Run from repo root:
    python3 scripts/generate-cookbook-index.py

Produces a deterministic MDX file. Run in CI to detect drift between the
filesystem and the committed page.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parent.parent
COOKBOOKS = ROOT / "cookbooks"
OUT = ROOT / "docs" / "cookbooks-index.mdx"

HEADER = """\
---
title: "Cookbook"
description: "Runnable, manifest-aligned ArcFlow recipes — every step CI-tested against the engine version it pins to."
section: "recipes"
status: "stable"
---

{/* AUTO-GENERATED FROM cookbooks/<recipe>/meta.toml — DO NOT EDIT BY HAND.
    Regenerate with: python3 scripts/generate-cookbook-index.py
    Governed by PAT-0044 (Cookbook Recipe Governance). */}

# Cookbook

Runnable, end-to-end ArcFlow recipes. Every recipe ships its data, runs
in CI on every commit, and uses only `status: shipped` APIs from
[`release-matrix.json`](https://pub-a0a196dbe10340f8af22524547fdd476.r2.dev/releases/arcflow/release-matrix.json).

The recipes live in [`cookbooks/`](https://github.com/ozinc/arcflow-docs/tree/main/cookbooks)
in this repository. Each recipe is a self-contained directory with its own
`README.md`, numbered steps, sample data, and `meta.toml`.

## Recipes

"""

FOOTER = """\

## Run a recipe locally

```bash
git clone https://github.com/ozinc/arcflow-docs
cd arcflow-docs/cookbooks/<recipe-slug>
uv sync                       # installs deps, including arcflow
uv run python 00-make-sample.py
uv run python 02-*.py
# ... continue through the numbered steps in order
```

ArcFlow itself is installed via the [InstallMatrix](/installation) — every
recipe references the same source of truth, so installation never drifts.

## Recipe governance

Recipes are governed by **PAT-0044** in the engine repository. See
[`cookbooks/CONTRIBUTING.md`](https://github.com/ozinc/arcflow-docs/blob/main/cookbooks/CONTRIBUTING.md)
for the operational summary. Key rules:

- Each recipe demonstrates one ArcFlow capability end-to-end.
- Recipes use only `status: shipped` ArcFlow APIs at the recipe's
  `meta.toml.manifest_pin`.
- Sample data is in-tree and ≤ 5 MB.
- CI runs every recipe end-to-end on every commit. Fail closed.
"""


def discover_recipes() -> list[dict]:
    if not COOKBOOKS.exists():
        return []

    skip = {"_template", "_demos", "_archive"}
    recipes: list[dict] = []

    for recipe_dir in sorted(COOKBOOKS.iterdir()):
        if not recipe_dir.is_dir():
            continue
        if recipe_dir.name in skip:
            continue
        meta_path = recipe_dir / "meta.toml"
        if not meta_path.exists():
            continue

        with meta_path.open("rb") as fh:
            meta = tomllib.load(fh)

        slug = meta.get("slug", recipe_dir.name)
        if slug != recipe_dir.name:
            print(
                f"  warn: {recipe_dir.name}/meta.toml has slug={slug!r} but "
                f"folder is {recipe_dir.name!r} — using folder name",
                file=sys.stderr,
            )
            slug = recipe_dir.name

        recipes.append(
            {
                "slug": slug,
                "title": meta.get("title", slug),
                "audience": meta.get("audience", []),
                "runtime_minutes": meta.get("runtime_minutes", 0),
                "manifest_pin": meta.get("manifest_pin", "—"),
                "gpu_required": meta.get("gpu_required", False),
            }
        )

    return recipes


def render_table(recipes: list[dict]) -> str:
    if not recipes:
        return "_No recipes available yet._\n"

    lines = [
        "| Recipe | Audience | Runtime | Engine | GPU |",
        "|---|---|---|---|---|",
    ]
    for r in recipes:
        slug = r["slug"]
        link = f"[{r['title']}](https://github.com/ozinc/arcflow-docs/tree/main/cookbooks/{slug})"
        audience = ", ".join(r["audience"]) if r["audience"] else "—"
        runtime = f"≤ {r['runtime_minutes']} min" if r["runtime_minutes"] else "—"
        engine = f"`{r['manifest_pin']}`"
        gpu = "yes" if r["gpu_required"] else "no"
        lines.append(f"| {link} | {audience} | {runtime} | {engine} | {gpu} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    recipes = discover_recipes()
    body = HEADER + render_table(recipes) + FOOTER
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if OUT.exists() and OUT.read_text() == body:
        print(f"unchanged: {OUT.relative_to(ROOT)}")
        return 0

    OUT.write_text(body)
    print(
        f"wrote {OUT.relative_to(ROOT)} — {len(recipes)} recipe(s) indexed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
