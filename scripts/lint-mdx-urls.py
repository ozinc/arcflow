#!/usr/bin/env python3
"""Lint docs/**/*.mdx for hardcoded customer-facing URLs.

P-93 (Deployment-Aware URL Resolution): customer-facing URLs are functions
of rendering context, not strings. The website's docs renderer rewrites
own-origin absolute URLs to relative paths at render time, but enforcing
the relative form *at the source* keeps the content portable to staging,
dev1, local, and any future deployment without surprise host literals.

Companion to oz-platform/apps/cloud/website/tests/unit/lint-disclosure-url.test.ts
which enforces the same rule on the website's TS/TSX/MDX/JSON sources.

Behaviour:
  - Scans every docs/**/*.mdx file.
  - Skips frontmatter (leading `---` block).
  - Skips fenced code blocks (``` ... ```), since command-line examples
    legitimately need absolute URLs (`curl -fsSL https://oz.com/install | sh`).
    Those are addressed by the T3 generator that produces literal install
    commands from `release-matrix.json`.
  - Fails on `https://oz.com` or `https://staging.oz.com` literals in prose.
  - Allows `docs/README.md`: it's GitHub-rendered as the docs landing pointer
    where the absolute host *is* the canonical reference.

Exit codes: 0 = clean, 1 = offenders found, 2 = no MDX files found.

See: kanban/patterns/design-patterns.md (P-93)
     kanban/patterns/antipatterns.md (AP-70)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"

# Files allowed to keep absolute oz.com URLs.
# - docs/README.md is rendered on GitHub (raw) where /docs would be wrong.
ALLOWLIST = {
    Path("docs/README.md"),
}

FORBIDDEN = re.compile(r"https://(?:staging\.)?oz\.com\b")


def strip_frontmatter_and_fences(text: str) -> list[tuple[int, str]]:
    """Yield (1-indexed line_number, line_text) pairs for prose-only content.

    Skips:
      - Leading frontmatter block (between first two `---` lines)
      - Fenced code blocks (``` ... ```)
    """
    lines = text.splitlines()
    out: list[tuple[int, str]] = []

    in_frontmatter = False
    in_fence = False
    fence_marker: str | None = None
    started_frontmatter = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Frontmatter detection — only at the very top of file.
        if not started_frontmatter and idx == 1 and stripped == "---":
            in_frontmatter = True
            started_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        # Fenced code blocks. ``` or ~~~ open/close. Track the marker so a
        # `~~~` block doesn't accidentally close on a `~~~~` (rare).
        fence_match = re.match(r"^(`{3,}|~{3,})", line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[:3]  # match either family
            elif marker.startswith(fence_marker or ""):
                in_fence = False
                fence_marker = None
            continue
        if in_fence:
            continue

        out.append((idx, line))

    return out


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (line, text) tuples that violate the rule."""
    text = path.read_text(encoding="utf-8")
    offenders: list[tuple[int, str]] = []
    for line_no, line in strip_frontmatter_and_fences(text):
        if FORBIDDEN.search(line):
            offenders.append((line_no, line.rstrip()))
    return offenders


def main() -> int:
    if not DOCS_DIR.is_dir():
        print(f"error: docs directory not found at {DOCS_DIR}", file=sys.stderr)
        return 2

    mdx_files = sorted(DOCS_DIR.rglob("*.mdx"))
    if not mdx_files:
        print(f"error: no MDX files under {DOCS_DIR}", file=sys.stderr)
        return 2

    total_offenders = 0
    for path in mdx_files:
        rel = path.relative_to(ROOT)
        if rel in ALLOWLIST:
            continue
        offenders = scan_file(path)
        if offenders:
            for line_no, text in offenders:
                print(f"{rel}:{line_no}: {text.strip()}")
            total_offenders += len(offenders)

    if total_offenders > 0:
        print()
        print(
            f"FAIL: {total_offenders} hardcoded customer-facing URL(s) in MDX prose.",
            file=sys.stderr,
        )
        print(
            "Resolution: use a site-relative path (`/docs/installation`, "
            "not `https://oz.com/docs/installation`). Install commands inside "
            "fenced code blocks are exempt — those flow through the T3 "
            "generator that reads `release-matrix.json`. See P-93 / AP-70.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: scanned {len(mdx_files)} MDX file(s); no hardcoded oz.com URLs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
