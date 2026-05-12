#!/usr/bin/env python3
"""
Structural lint for the /spec/ surface — generated dashboards (GQL features,
conformance, vendor extensions). Sibling to /docs/.

Reads spec/_config.json and spec/**/*.mdx.

Rules:
  S1   Every .mdx in spec/ is registered in spec/_config.json.
  S2   Every registered slug has a backing .mdx file.
  S3   No two registered slugs collide.
  S4   schema_version is "v2".
  S5   No frontmatter `section:` (config is sole SSoT).

Thinner than the /docs/ lint — /spec/ has no kind-mapping, no canonicals,
no facets.

Run: scripts/check-spec-structure.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec"
CONFIG = SPEC / "_config.json"


def load_config() -> dict:
    return json.loads(CONFIG.read_text())


def all_mdx_files() -> list[Path]:
    return sorted(p for p in SPEC.rglob("*.mdx"))


def mdx_to_slug(path: Path) -> str:
    rel = path.relative_to(SPEC).with_suffix("")
    parts = rel.parts
    if parts[-1] == "index":
        parts = parts[:-1]
    return "/".join(parts)


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    fm: dict[str, object] = {}
    for line in text[4:end].splitlines():
        line = line.rstrip()
        if not line or ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def flatten_items(items: list[dict]) -> list[dict]:
    out = []
    for it in items:
        if it.get("slug"):
            out.append(it)
        if it.get("children"):
            out.extend(flatten_items(it["children"]))
    return out


def main() -> int:
    if not CONFIG.exists():
        print(f"S0: spec/_config.json missing — DIA Phase 2 incomplete?", file=sys.stderr)
        return 1

    cfg = load_config()
    mdx_files = all_mdx_files()
    errors: list[str] = []

    # S4
    if cfg.get("schema_version") != "v2":
        errors.append(f"S4: spec/_config.json schema_version='{cfg.get('schema_version')}' — expected 'v2'")

    # S1/S2/S3
    registered: set[str] = set()
    seen: dict[str, str] = {}
    for section in cfg["sections"]:
        sid = section["id"]
        for item in flatten_items(section["items"]):
            slug = item["slug"]
            if slug in seen:
                errors.append(f"S3: slug '{slug}' duplicated ({seen[slug]} + {sid})")
            else:
                seen[slug] = sid
                registered.add(slug)

    mdx_slugs = {mdx_to_slug(p): p for p in mdx_files}
    for slug, path in mdx_slugs.items():
        if slug not in registered:
            errors.append(f"S1: {path.relative_to(ROOT)} (slug='{slug}') not in spec/_config.json")
    for slug in registered:
        if slug not in mdx_slugs and not (SPEC / f"{slug}.mdx").exists() and not (SPEC / slug / "index.mdx").exists():
            errors.append(f"S2: registered slug '{slug}' has no backing file in spec/")

    # S5
    for path in mdx_files:
        fm = parse_frontmatter(path)
        if "section" in fm:
            errors.append(f"S5: {path.relative_to(ROOT)} has deprecated frontmatter `section:`")

    if errors:
        print(f"Spec structure: {len(errors)} issue(s)\n", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"Spec structure: clean ({len(mdx_files)} MDX, {len(registered)} registered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
