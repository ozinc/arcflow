#!/usr/bin/env python3
"""Lint: hardcoded ArcFlow version literals outside permitted SoT-bearing files.

Rule: version literals matching the current `0.x` alpha-state line (e.g.
"0.7.1"), the pre-revision `1.6.x` line (e.g. "1.6.86"), or the legacy engine
FFI literal ("5.1.0") must NOT appear in prose docs, MDX, illustrative
examples, or cookbook narrative outside an explicit allow-list of SoT-bearing
files. The SoT is the manifest at release-matrix.json (attached to each
GitHub Release); everything else either reads from the manifest at
render/runtime or is explicitly listed in the allow-list below as a
SoT-bearing file (e.g. cookbook pyproject.toml pins, install.sh env-var
example).

Run: python3 scripts/lint-version-literals.py
Exit code: 0 if clean, 1 on first violation.

Companion of P-93 (URL Discipline). See docs/reference/versioning.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Matches current ArcFlow version literals across both the alpha-state `0.x`
# line and the pre-revision `1.6.x` line, plus the legacy FFI form "5.1.0"
# pre-convergence. Bounds with non-digit boundaries to avoid false positives.
VERSION_PATTERN = re.compile(
    r"(?<![0-9])(?:0\.7\.\d+|1\.6\.\d+|5\.1\.0)(?![0-9])"
)

# Files PERMITTED to contain hardcoded version literals.
# Categories:
#   (a) The actual SoT (SYNC.json)
#   (b) Build-time consumers that pin literal versions (cookbook pyproject.toml)
#   (c) Historical record (federation receipts)
#   (d) Scripts that resolve runtime versions (install.sh — has example values)
#   (e) Illustrative samples in prose (license clauses, attestation walkthroughs,
#       sample JSON responses) — bumped on release; TODO(refactor): replace with
#       manifest-render at MDX render time once oz-platform ships the substitution.
#   (f) Governance / project docs that intentionally cite versions for context
#       (CLAUDE.md historical context, AGENTS.md install examples).
ALLOWLIST_FILES = {
    # SoT in this repo
    "docs/reference/data/SYNC.json",
    "scripts/lint-version-literals.py",  # self-referent: this lint regex IS the pattern
    # Build-time consumers (one literal per release; bumped on tag)
    "create-arcflow/templates/python/pyproject.toml",
    "examples/_template/meta.toml",
    "examples/_template/pyproject.toml",
    "examples/run-ci.sh",
    "examples/CONTRIBUTING.md",
    ".github/workflows/cookbook-test.yml",
    "install/install.sh",
    # Versioning doc itself (cites version literals as examples — that's its job)
    "docs/reference/versioning.mdx",
    # Governance / project docs
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "ARCFLOW_FOR_AI_AGENTS.md",
    # License discussion documents (cite specific shipped versions)
    "LICENSE-FAQ.md",
    "LICENSE-CORE.md",
    # Illustrative prose / sample responses — currently hand-bumped; manifest-sourced when OZ ships substitution
    "docs/reproducible-build.md",
    "docs/protocol/jsonrpc-v1.md",
    "docs/deployment/daemon.mdx",
    # The four version-description surfaces — show users what each call returns
    "docs/bindings.mdx",
    "docs/server/index.mdx",
    "docs/guides/sql-to-gql.mdx",
    # Independent version concepts (not engine version)
    "docs/reference/worldcypher.yaml",                  # WorldCypher SPEC version
    "docs/reference/data/arcflow-extensions-catalog.md",  # extensions catalog document version
    # "Since" feature-introduction column — TODO(tech-debt): align with no-version-temporal memory rule
    "docs/worldcypher/functions/procedures.mdx",
    # Conformance dashboard entries DROPPED 2026-05-16 — AF-DOC-2026-05-16-003-ssot-closure
    # shipped the temporal-noise strip upstream (commit 8421be0b); engine version + date
    # fields no longer appear in gql-conformance.json or its rendered MDX. Lint-version-
    # literals.py no longer needs an exception for these three files.
}

ALLOWLIST_PATTERNS = [
    # Cookbook pyproject + meta files — each cookbook owns its pin
    re.compile(r"^examples/[^/]+/(pyproject\.toml|meta\.toml)$"),
    # Cookbook README "Pins:" header line — currently bumped by hand each release
    # TODO(refactor): replace with manifest-render at MDX render time on oz-platform side.
    re.compile(r"^examples/[^/]+/README\.md$"),
    # Internal planning / roadmap / federation receipts — not a customer-facing
    # version surface (per CLAUDE.md, all of kanban/ is internal planning).
    re.compile(r"^kanban/"),
    # npm/yarn package locks contain unrelated third-party package versions
    re.compile(r"(^|/)package-lock\.json$"),
    re.compile(r"(^|/)yarn\.lock$"),
    re.compile(r"(^|/)pnpm-lock\.yaml$"),
]

# Extensions to scan
SCAN_EXTS = {
    ".md",
    ".mdx",
    ".py",
    ".sh",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".ts",
    ".tsx",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
    "target",
    "dist",
    "build",
    ".next",
    "wheels",
}


def is_allowlisted(rel_path: str) -> bool:
    if rel_path in ALLOWLIST_FILES:
        return True
    for pat in ALLOWLIST_PATTERNS:
        if pat.search(rel_path):
            return True
    return False


def scan() -> int:
    violations: list[tuple[str, int, str]] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in SCAN_EXTS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if is_allowlisted(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in VERSION_PATTERN.finditer(line):
                violations.append((rel, lineno, line.strip()))
                break  # one hit per line is enough

    if not violations:
        print("OK — no hardcoded ArcFlow version literals outside SoT-bearing files.")
        return 0

    print(
        f"Hardcoded ArcFlow version literals found in {len(violations)} non-allowlisted location(s):\n"
    )
    for rel, lineno, line in violations:
        print(f"  {rel}:{lineno}")
        print(f"    {line[:160]}")
    print()
    print(
        "Fix: read the value from release-matrix.json at render/runtime, "
        "or add the file to ALLOWLIST_FILES / ALLOWLIST_PATTERNS in this script "
        "if it's an intentional SoT-bearing surface. See docs/reference/versioning."
    )
    return 1


if __name__ == "__main__":
    sys.exit(scan())
