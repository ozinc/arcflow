#!/usr/bin/env python3
"""Lint for hand-rolled install commands in arcflow-docs.

Enforces PAT-0043 (Manifest-Driven Install Disclosure):
every public install command flows from release-matrix.json via the
<InstallMatrix /> MDX component (rendered by oz-platform).

This script greps the docs/, install/, llms.txt, llms-full.txt surfaces for
literal install command patterns. Any match outside the allowlist is a
CI failure.

Run:
    python3 scripts/lint-install-commands.py

CI: .github/workflows/lint-install-commands.yml
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Patterns forbidden in customer-facing surfaces. Each is a literal install
# command an LLM agent or human reader could copy-paste.
FORBIDDEN_PATTERNS = [
    # pip — both the legacy `arcflow` distribution name and the current
    # `oz-arcflow` distribution name are forbidden in hand-rolled prose.
    re.compile(r"\bpip install arcflow\b"),
    re.compile(r"\bpip install oz-arcflow\b"),
    # npm — both bare and scoped (`@ozinc/arcflow`) are forbidden.
    re.compile(r"\bnpm install arcflow\b"),
    re.compile(r"\bnpm install @ozinc/arcflow\b"),
    # cargo
    re.compile(r"\bcargo add arcflow\b"),
    re.compile(r"\bcargo install arcflow\b"),
    # docker
    re.compile(r"ghcr\.io/[A-Za-z0-9._-]+/arcflow"),
    # legacy installer asset path
    re.compile(r"/install_arcflow\b"),
]

# Surfaces the lint scans.
SCAN_PATHS = [
    ROOT / "docs",
    ROOT / "install" / "README.md",
    ROOT / "llms.txt",
    ROOT / "llms-full.txt",
]

# Files where references to the forbidden patterns are intentional and
# allowed:
#   - planning/   architectural docs that describe the rule itself
#   - examples/  recipe meta.toml may reference api strings; pyproject.toml
#                 may reference local wheel paths (not registry installs)
#   - this script
#   - schemas/release-matrix.schema.json (descriptive examples)
ALLOWLIST_DIRS = [
    ROOT / "planning",
    ROOT / "cookbooks",
    ROOT / "schemas",
]
ALLOWLIST_FILES = [
    ROOT / "scripts" / "lint-install-commands.py",
]

# Specific files inside scan paths that are allowed to mention forbidden
# patterns illustratively (e.g., licensing.mdx refers to "from a user
# perspective `npm install arcflow` just works" as forward-looking copy).
# Each entry must include a justification.
SOFT_ALLOWLIST: dict[Path, str] = {
    ROOT / "docs" / "licensing.mdx": (
        "Licensing page describes future-state user experience; the npm/pip "
        "references are aspirational copy, not install instructions. They "
        "stay until those bindings ship and the copy can shift to past tense."
    ),
    ROOT / "docs" / "_agent-optimization.md": (
        "Internal agent-optimization notes describe the future install "
        "experience; not a customer-facing install surface."
    ),
}


def is_allowlisted(path: Path) -> bool:
    if path in ALLOWLIST_FILES or path in SOFT_ALLOWLIST:
        return True
    for d in ALLOWLIST_DIRS:
        try:
            path.relative_to(d)
            return True
        except ValueError:
            continue
    return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, pattern, line) tuples for matches in `path`."""
    matches: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return matches
    for n, line in enumerate(text.splitlines(), start=1):
        for pat in FORBIDDEN_PATTERNS:
            if pat.search(line):
                matches.append((n, pat.pattern, line.strip()))
                break
    return matches


def iter_targets() -> list[Path]:
    files: list[Path] = []
    for p in SCAN_PATHS:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file() and sub.suffix in {".mdx", ".md", ".txt"}:
                    files.append(sub)
    return files


def main() -> int:
    failures: list[tuple[Path, int, str, str]] = []
    softs: list[tuple[Path, int, str]] = []

    for f in iter_targets():
        if is_allowlisted(f):
            continue
        for n, pat, line in scan_file(f):
            if f in SOFT_ALLOWLIST:
                softs.append((f, n, line))
            else:
                failures.append((f, n, pat, line))

    if softs:
        print("Soft-allowlisted matches (informational, not failing CI):")
        for f, n, line in softs:
            rel = f.relative_to(ROOT)
            print(f"  {rel}:{n}  {line}")
        print()

    if failures:
        print("Forbidden hand-rolled install commands (PAT-0043 violation):")
        for f, n, pat, line in failures:
            rel = f.relative_to(ROOT)
            print(f"  ✗ {rel}:{n}  matched {pat!r}")
            print(f"      {line}")
        print()
        print(
            "Resolution: replace with <InstallMatrix /> MDX component, or "
            "delete. See PAT-0043 in arcflow/kanban/patterns/."
        )
        return 1

    print("OK — no hand-rolled install commands in customer-facing surfaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
