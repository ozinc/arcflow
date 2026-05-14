#!/usr/bin/env python3
"""Lint: hardcoded ArcFlow version literals outside permitted SoT-bearing files.

Rule: version literals matching the SDK distribution version (e.g. "1.6.86") or
the legacy engine FFI version (e.g. "5.1.0") must NOT appear in prose docs,
MDX, illustrative examples, or cookbook narrative. The SoT is the manifest at
release-matrix.json (rendered from the git tag of arcflow-core); everything
else either reads from the manifest at render/runtime or is explicitly listed
in the allow-list below as a SoT-bearing file (e.g. cookbook pyproject.toml
pins, install.sh env-var example).

Run: python3 scripts/lint-version-literals.py
Exit code: 0 if clean, 1 on first violation.

Companion of P-93 (URL Discipline). See docs/reference/versioning.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Matches the SDK-distribution shape "X.Y.Z" where X is single digit 1, Y/Z
# can be multi-digit. Bounds with non-digit / start-of-word.
# Also catches the legacy engine FFI form "5.1.0" pre-convergence.
VERSION_PATTERN = re.compile(
    r"(?<![0-9])(?:1\.6\.\d+|5\.1\.0)(?![0-9])"
)

# Files PERMITTED to contain hardcoded version literals.
# Categories:
#   (a) The actual SoT (SYNC.json)
#   (b) Build-time consumers that pin literal versions (cookbook pyproject.toml)
#   (c) Historical record (CHANGELOG, federation receipts)
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
    "cookbooks/_template/meta.toml",
    "cookbooks/_template/pyproject.toml",
    "cookbooks/run-ci.sh",
    "cookbooks/CONTRIBUTING.md",
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
    # Conformance dashboard — engine version row.
    # SoT: upstream arcflow-core/docs/conformance/gql-conformance.json (synced
    # by scripts/sync-conformance-data.sh) and rendered by generate-reference.py.
    # TODO(refactor): source from release-matrix.json at render time so the
    # literal disappears. Tracked via federation request DOC-AF-versioning-ssot.
    "docs/reference/data/gql-conformance.json",
    "docs/reference/gql-conformance.mdx",
    "docs/reference/conformance/overview.mdx",
}

ALLOWLIST_PATTERNS = [
    # Cookbook pyproject + meta files — each cookbook owns its pin
    re.compile(r"^cookbooks/[^/]+/(pyproject\.toml|meta\.toml)$"),
    # Cookbook README "Pins:" header line — currently bumped by hand each release
    # TODO(refactor): replace with manifest-render at MDX render time on oz-platform side.
    re.compile(r"^cookbooks/[^/]+/README\.md$"),
    # Federation receipts — immutable audit trail
    re.compile(r"^kanban/federation/"),
    # Historical CHANGELOG
    re.compile(r"^CHANGELOG\.md$"),
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
