#!/usr/bin/env python3
"""
Structural integrity linter for the docs repo.

Enforces the durable-vs-intake split documented in docs/CONTRIBUTING.md:

  R1. Every .mdx in docs/ is registered in docs/_config.json
      (or is an index.mdx whose parent slug is registered).
  R2. Every registered slug has a backing file.
  R3. No two registered slugs collide.
  R4. Pages with `generated: true` frontmatter live only under docs/reference/.
  R5. Pages under docs/reference/{gql,extensions}/ all have `generated: true`.
  R6. Sections marked `"managed": ...` in _config.json are owned by that
      script — they should match what the generator produces (delegated to
      `scripts/generate-reference.py --check`; this linter only enforces the
      `managed` metadata field is present on the right sections).

Exit codes:
  0  — clean
  1  — structural drift detected

Run: scripts/check-docs-structure.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = DOCS / "_config.json"

MANAGED_SECTIONS = {"gql-conformance", "gql-features", "arcflow-extensions"}
GENERATED_DIRS = {"reference/gql", "reference/extensions"}
GENERATED_TOP_PAGES = {
    "reference/gql-conformance",
    "reference/tck",
    "reference/extensions-regressions",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    return json.loads(CONFIG.read_text())


def all_mdx_files() -> list[Path]:
    return sorted(p for p in DOCS.rglob("*.mdx"))


def mdx_to_slug(path: Path) -> str:
    """docs/foo/bar.mdx → foo/bar; docs/foo/index.mdx → foo (or foo/index)."""
    rel = path.relative_to(DOCS).with_suffix("")
    parts = rel.parts
    if parts[-1] == "index":
        parts = parts[:-1]
    return "/".join(parts)


def parse_frontmatter(path: Path) -> dict:
    """Tiny YAML-subset parser — handles the flat key: value frontmatter we emit."""
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    fm = {}
    for line in text[4:end].splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip().strip('"').strip("'")
        if v.lower() in ("true", "false"):
            fm[k.strip()] = v.lower() == "true"
        else:
            fm[k.strip()] = v
    return fm


def collect_registered_slugs(cfg: dict) -> tuple[set[str], list[tuple[str, str]]]:
    """Returns (set of registered slugs, list of (slug, section_id) duplicates)."""
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for section in cfg["sections"]:
        sid = section["id"]
        for item in section["items"]:
            slug = item["slug"]
            if slug in seen:
                duplicates.append((slug, f"{seen[slug]} + {sid}"))
            else:
                seen[slug] = sid
    return set(seen), duplicates


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def check_r1_r2_r3(cfg: dict, mdx_files: list[Path]) -> list[str]:
    """R1 (every MDX registered), R2 (every slug has a file), R3 (no slug collision)."""
    errors: list[str] = []
    registered, duplicates = collect_registered_slugs(cfg)

    # R3: collisions
    for slug, where in duplicates:
        errors.append(f"R3: slug '{slug}' is registered twice ({where})")

    # R1: every MDX must be registered (with index.mdx fallback)
    mdx_slugs = {mdx_to_slug(p): p for p in mdx_files}
    for slug, path in mdx_slugs.items():
        if slug in registered:
            continue
        # Tolerate index.mdx being registered under either form
        if path.name == "index.mdx" and f"{slug}/index" in registered:
            continue
        rel = path.relative_to(ROOT)
        errors.append(f"R1: {rel} (slug='{slug}') is not registered in _config.json")

    # R2: every registered slug must have a file
    available = set(mdx_slugs)
    available |= {f"{s}/index" for s in mdx_slugs}
    for slug in registered:
        if slug in available:
            continue
        # Try parent/index form (slug 'foo' may resolve to docs/foo/index.mdx)
        if (DOCS / slug / "index.mdx").exists():
            continue
        if (DOCS / f"{slug}.mdx").exists():
            continue
        errors.append(f"R2: registered slug '{slug}' has no backing .mdx file")

    return errors


def check_r4_r5(mdx_files: list[Path]) -> list[str]:
    """R4: generated frontmatter only under docs/reference/.
       R5: pages under reference/gql or reference/extensions must be generated."""
    errors: list[str] = []
    for path in mdx_files:
        rel = path.relative_to(DOCS).as_posix()
        fm = parse_frontmatter(path)
        is_generated = bool(fm.get("generated"))

        if is_generated and not rel.startswith("reference/"):
            errors.append(f"R4: {path.relative_to(ROOT)} has generated:true but is outside docs/reference/")

        if rel.startswith(("reference/gql/", "reference/extensions/")) and not is_generated:
            errors.append(f"R5: {path.relative_to(ROOT)} is in a generated directory but missing generated:true")

    return errors


def check_r6(cfg: dict) -> list[str]:
    """R6: managed sections must declare a `managed` field naming their generator."""
    errors: list[str] = []
    for section in cfg["sections"]:
        sid = section.get("id")
        if sid in MANAGED_SECTIONS and "managed" not in section:
            errors.append(f"R6: section '{sid}' must declare a 'managed' field naming its generator")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    cfg = load_config()
    mdx_files = all_mdx_files()

    all_errors: list[str] = []
    all_errors += check_r1_r2_r3(cfg, mdx_files)
    all_errors += check_r4_r5(mdx_files)
    all_errors += check_r6(cfg)

    if all_errors:
        print(f"Docs structure: {len(all_errors)} issue(s) found\n", file=sys.stderr)
        # Group by rule for legibility
        by_rule: dict[str, list[str]] = {}
        for e in all_errors:
            rule = e.split(":", 1)[0]
            by_rule.setdefault(rule, []).append(e)
        for rule in sorted(by_rule):
            print(f"\n{rule}:", file=sys.stderr)
            for e in by_rule[rule]:
                print(f"  {e[len(rule) + 2:]}", file=sys.stderr)
        print(f"\nTotal: {len(all_errors)} issue(s)", file=sys.stderr)
        print("See docs/CONTRIBUTING.md for the rules.", file=sys.stderr)
        return 1

    print(f"Docs structure: clean ({len(mdx_files)} MDX files, "
          f"{sum(len(s['items']) for s in cfg['sections'])} sidebar entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
