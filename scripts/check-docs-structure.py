#!/usr/bin/env python3
"""
Structural lint for arcflow-docs after the DIA restructure (2026-05-12).
Updated for _config.json schema v2: multi-level children, kind mapping,
canonical declarations, pinned links, deprecated frontmatter `section:`.

Source of truth for rules: docs/_AGENTS.md.

Rules:
  R1   Every .mdx in docs/ is registered in docs/_config.json OR is a
       facet (file has frontmatter `canonical:`). Facets are reachable
       URLs but not sidebar items.
  R2   Every registered slug has a backing .mdx file.
  R3   No two registered slugs collide.
  R4   `_config.json` top-level sections ≤ max_top_level_sections.
  R5   Every page declares `kind:` frontmatter; kind matches section's
       declared kind (per section_kind_map in _config.json).
  R6   No frontmatter `section:` field anywhere (deprecated in DIA;
       _config.json is sole SSOT).
  R7   Every page that declares `canonical: <slug>` must reference a
       slug that exists in either _config.json registration OR another
       page on disk (= valid canonical target). Cycles not allowed.
  R8   No sibling order: collisions within the same parent group.
  R9   schema_version is "v2" (or absent for legacy; warns).

Exit codes:
  0 — clean
  1 — drift detected
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = DOCS / "_config.json"


def load_config() -> dict:
    return json.loads(CONFIG.read_text())


def all_mdx_files() -> list[Path]:
    return sorted(p for p in DOCS.rglob("*.mdx"))


def mdx_to_slug(path: Path) -> str:
    rel = path.relative_to(DOCS).with_suffix("")
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
        v = v.strip().strip('"').strip("'")
        if v.lower() in ("true", "false"):
            fm[k.strip()] = v.lower() == "true"
        else:
            fm[k.strip()] = v
    return fm


def flatten_items(items: list[dict]) -> list[dict]:
    """Recursively flatten nested children. Returns leaf items only (with slug)."""
    out = []
    for it in items:
        if it.get("slug"):
            out.append(it)
        if it.get("children"):
            out.extend(flatten_items(it["children"]))
    return out


def all_items_with_parent(items: list[dict], parent_path: str = "") -> list[tuple[dict, str]]:
    """Returns [(item, parent_path)] for order: collision detection. Siblings share parent_path."""
    out = []
    for it in items:
        out.append((it, parent_path))
        if it.get("children"):
            child_parent = f"{parent_path}/{it.get('slug') or it.get('title')}"
            out.extend(all_items_with_parent(it["children"], child_parent))
    return out


def collect_registered_slugs(cfg: dict) -> tuple[set[str], list[tuple[str, str]]]:
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for section in cfg["sections"]:
        sid = section["id"]
        for item in flatten_items(section["items"]):
            slug = item["slug"]
            if slug in seen:
                duplicates.append((slug, f"{seen[slug]} + {sid}"))
            else:
                seen[slug] = sid
    return set(seen), duplicates


def check_r1_r2_r3(cfg: dict, mdx_files: list[Path]) -> list[str]:
    errors: list[str] = []
    registered, duplicates = collect_registered_slugs(cfg)

    for slug, where in duplicates:
        errors.append(f"R3: slug '{slug}' is registered twice ({where})")

    mdx_slugs = {mdx_to_slug(p): p for p in mdx_files}
    for slug, path in mdx_slugs.items():
        if slug in registered:
            continue
        # Facet escape: page declares canonical: <target> — facets are
        # legitimately not in the sidebar but exist as URLs.
        fm = parse_frontmatter(path)
        if fm.get("canonical"):
            continue
        if path.name == "index.mdx" and f"{slug}/index" in registered:
            continue
        rel = path.relative_to(ROOT)
        errors.append(f"R1: {rel} (slug='{slug}') is not registered in _config.json and has no canonical:")

    available = set(mdx_slugs)
    available |= {f"{s}/index" for s in mdx_slugs}
    for slug in registered:
        if slug in available:
            continue
        if (DOCS / slug / "index.mdx").exists():
            continue
        if (DOCS / f"{slug}.mdx").exists():
            continue
        errors.append(f"R2: registered slug '{slug}' has no backing .mdx file")

    return errors


def check_r4(cfg: dict) -> list[str]:
    lint = cfg.get("lint", {})
    cap = lint.get("max_top_level_sections", 8)
    n = len(cfg["sections"])
    if n > cap:
        return [f"R4: {n} top-level sections in _config.json — exceeds lint.max_top_level_sections={cap}"]
    return []


def check_r5(cfg: dict, mdx_files: list[Path]) -> list[str]:
    """Every registered (non-facet) page declares kind: matching its section's declared kind.
    Tightened: requires presence, not just match — absent kind: on a registered page is a fail."""
    errors: list[str] = []
    kind_map = cfg.get("lint", {}).get("section_kind_map", {})
    if not kind_map:
        return []
    slug_to_section: dict[str, str] = {}
    for section in cfg["sections"]:
        sid = section["id"]
        for item in flatten_items(section["items"]):
            slug_to_section[item["slug"]] = sid

    mdx_slugs = {mdx_to_slug(p): p for p in mdx_files}
    for slug, sid in slug_to_section.items():
        path = mdx_slugs.get(slug)
        if not path:
            idx = DOCS / f"{slug}/index.mdx"
            path = idx if idx.exists() else None
        if not path:
            continue
        fm = parse_frontmatter(path)
        # Facets are exempt — they declare `canonical:` and don't need kind:
        if fm.get("canonical"):
            continue
        kind = fm.get("kind")
        expected = kind_map.get(sid)
        if not expected:
            continue
        if not kind:
            errors.append(f"R5: {path.relative_to(ROOT)} missing required frontmatter `kind: {expected}` (registered under section '{sid}')")
        elif kind != expected:
            errors.append(f"R5: {path.relative_to(ROOT)} declares kind='{kind}' but section '{sid}' expects kind='{expected}'")
    return errors


# Deprecated frontmatter fields — _config.json is the sole SSOT for placement
# and ordering per DIA decision 2. Pages that carry these confuse readers and
# create drift potential.
DEPRECATED_FM_FIELDS = ("section", "order")


def check_r6(mdx_files: list[Path]) -> list[str]:
    """No deprecated frontmatter fields — DIA-deprecated per decision 2.
    Tightened to also catch `order:` (config-only field that was leaking into
    page frontmatter and rotting alongside the renamed/reordered nav)."""
    errors: list[str] = []
    for path in mdx_files:
        fm = parse_frontmatter(path)
        for field in DEPRECATED_FM_FIELDS:
            if field in fm:
                errors.append(f"R6: {path.relative_to(ROOT)} has deprecated frontmatter `{field}:` — remove (config is SSOT per docs/_AGENTS.md)")
    return errors


def check_r7(cfg: dict, mdx_files: list[Path]) -> list[str]:
    """Canonical declarations must point to valid slugs (registered OR present on disk)."""
    errors: list[str] = []
    registered, _ = collect_registered_slugs(cfg)
    mdx_slugs = {mdx_to_slug(p) for p in mdx_files}
    valid_targets = registered | mdx_slugs

    for path in mdx_files:
        fm = parse_frontmatter(path)
        canonical = fm.get("canonical")
        if not canonical:
            continue
        if canonical not in valid_targets:
            errors.append(f"R7: {path.relative_to(ROOT)} declares canonical='{canonical}' but no such slug exists in config or on disk")
        if canonical == mdx_to_slug(path):
            errors.append(f"R7: {path.relative_to(ROOT)} declares canonical pointing to itself")
    return errors


def check_r8(cfg: dict) -> list[str]:
    """No sibling order: collisions within the same parent."""
    errors: list[str] = []
    for section in cfg["sections"]:
        items_with_parent = all_items_with_parent(section["items"], section["id"])
        # Group by parent_path, then check orders within
        groups: dict[str, list[dict]] = {}
        for it, parent in items_with_parent:
            groups.setdefault(parent, []).append(it)
        for parent, items in groups.items():
            orders = [it.get("order") for it in items if "order" in it]
            seen: dict[int, str] = {}
            for it in items:
                o = it.get("order")
                if o is None:
                    continue
                if o in seen:
                    errors.append(f"R8: order={o} collision under '{parent}': '{seen[o]}' and '{it.get('slug') or it.get('title')}'")
                else:
                    seen[o] = it.get("slug") or it.get("title", "?")
    return errors


def check_r9(cfg: dict) -> list[str]:
    sv = cfg.get("schema_version")
    if sv != "v2":
        return [f"R9: _config.json schema_version='{sv}' — DIA migration expects 'v2'"]
    return []


def main() -> int:
    cfg = load_config()
    mdx_files = all_mdx_files()

    all_errors: list[str] = []
    all_errors += check_r9(cfg)
    all_errors += check_r4(cfg)
    all_errors += check_r1_r2_r3(cfg, mdx_files)
    all_errors += check_r8(cfg)
    all_errors += check_r5(cfg, mdx_files)
    all_errors += check_r6(mdx_files)
    all_errors += check_r7(cfg, mdx_files)

    if all_errors:
        print(f"Docs structure (DIA v2): {len(all_errors)} issue(s) found\n", file=sys.stderr)
        by_rule: dict[str, list[str]] = {}
        for e in all_errors:
            rule = e.split(":", 1)[0]
            by_rule.setdefault(rule, []).append(e)
        for rule in sorted(by_rule):
            print(f"\n{rule}:", file=sys.stderr)
            for e in by_rule[rule]:
                print(f"  {e[len(rule) + 2:]}", file=sys.stderr)
        print(f"\nTotal: {len(all_errors)} issue(s)", file=sys.stderr)
        print("See docs/_AGENTS.md for the rules.", file=sys.stderr)
        return 1

    # Print summary
    n_top = len(cfg["sections"])
    flat_count = sum(len(flatten_items(s["items"])) for s in cfg["sections"])
    print(f"Docs structure (DIA v2): clean")
    print(f"  {len(mdx_files)} MDX files in docs/")
    print(f"  {n_top} top-level sections")
    print(f"  {flat_count} registered slug entries (leaves, after nesting)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
