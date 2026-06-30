#!/usr/bin/env python3
"""
Generate per-feature MDX reference pages from vendored conformance data.

Inputs (vendored by scripts/sync-conformance-data.sh):
    docs/reference/data/gql-conformance.json
    docs/reference/data/arcflow-extensions-catalog.md
    docs/reference/data/conformance-state.json
    docs/reference/data/SYNC.json

Outputs (regenerated each run, never hand-edited):
    docs/reference/gql-conformance.mdx     — dashboard
    docs/reference/tck.mdx                 — TCK summary
    docs/reference/gql/{slug}.mdx          — one per features.{key}
    docs/reference/extensions/{slug}.mdx   — one per ## section in catalog .md

Stdlib only. Run: scripts/generate-reference.py [--check]

  --check  : write to a temp dir and diff against tree (CI mode); exit 1 if drift.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "reference" / "data"
REFDIR = ROOT / "docs" / "reference"


def mdx_safe(text: str) -> str:
    """Escape `<` and `>` so MDX doesn't parse them as JSX tags.

    Notes like ``LIST<INT>/LIST<FLOAT>`` or ``USE GRAPH <name> clause``
    contain literal angle brackets that look like JSX element openers to
    the MDX compiler. With no matching close tag the page fails to compile
    and falls through to notFound() in the docs route. HTML entities
    render as the literal `<` / `>` characters in the rendered page.
    """
    return text.replace("<", "&lt;").replace(">", "&gt;")

GENERATED_HEADER = (
    "{/* GENERATED — do not hand-edit. "
    "Source: docs/reference/data/. "
    "Regenerate with scripts/generate-reference.py. */}"
)

# Tokens that should stay uppercase in titles (otherwise title-case)
UPPER_TOKENS = {
    "GQL", "GQLSTATUS", "MATCH", "RETURN", "WITH", "SET", "MERGE", "DELETE",
    "REMOVE", "CREATE", "WHERE", "UNWIND", "OPTIONAL", "CASE", "WHEN", "THEN",
    "ELSE", "NEXT", "USE", "FILTER", "LET", "FOR", "IN", "IS", "NOT", "ALL",
    "DISTINCT", "EXCEPT", "INTERSECT", "UNION", "TCK", "ID", "PK", "AS", "OF",
    "INT64", "BIGINT", "FLOAT64", "FROM", "BY", "TO", "ON", "OR", "AND", "API",
    "CLI", "WAL", "SDK", "AI", "ASOF", "HNSW", "GPU", "CDC", "REPL", "CTE",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> dict:
    return {
        "conformance": json.loads((DATA / "gql-conformance.json").read_text()),
        "state": json.loads((DATA / "conformance-state.json").read_text()),
        "sync": json.loads((DATA / "SYNC.json").read_text()),
        "extensions_md": (DATA / "arcflow-extensions-catalog.md").read_text(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def humanize_key(key: str) -> str:
    """match_basic → MATCH (basic);  arcflow_cosine_function → arcflow.cosine() function"""
    if key.startswith("arcflow_") and key.endswith(("_function", "_procedure")):
        # arcflow_cosine_function → arcflow.cosine()
        body = key[len("arcflow_"):]
        suffix = "function" if body.endswith("_function") else "procedure"
        body = body[: -(len(suffix) + 1)]
        return f"arcflow.{body}() {suffix}"

    parts = key.split("_")
    out = []
    for p in parts:
        u = p.upper()
        if u in UPPER_TOKENS:
            out.append(u)
        else:
            out.append(p.capitalize())
    return " ".join(out)


def slugify_key(key: str) -> str:
    return key.replace("_", "-")


def status_badge(status: str) -> str:
    return {
        "SUPPORTED": "**Supported**",
        "UNSUPPORTED": "**Not supported** _(vendor choice)_",
    }.get(status, f"**{status}**")


def phase_label(since: str | None, conformance: dict) -> str | None:
    """Map a `since` token (e.g. 'GQL-0003', 'GQLF-0002', 'EXT-0001') to a label."""
    if not since:
        return None
    if since in conformance.get("phases", {}):
        ph = conformance["phases"][since]
        return f"{since} — {ph['name'].replace('_', ' ')}"
    if since.startswith("GQLF-"):
        return f"{since} (GQL-Native Features track)"
    if since.startswith("GQLC-"):
        return f"{since} (Conformance track)"
    if since.startswith("EXT-"):
        return f"{since} (ArcFlow extension)"
    if since.startswith("PAT-"):
        return f"{since} (Pattern initiative)"
    return since


def provenance_footer(sync: dict, source_field: str) -> str:
    return (
        f"\n---\n\n"
        f"_Source: `docs/reference/data/{source_field}`. "
        f"This page is regenerated; edit the upstream data, not the MDX._\n"
    )


def write_if_changed(path: Path, content: str) -> bool:
    """Write only if content differs. Returns True if written."""
    if path.exists() and path.read_text() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


# ---------------------------------------------------------------------------
# GQL feature pages
# ---------------------------------------------------------------------------

def render_gql_feature(key: str, feat: dict, conformance: dict, sync: dict) -> str:
    title = humanize_key(key)
    status = feat.get("status", "UNKNOWN")
    since = feat.get("since")
    track = feat.get("track")
    note = feat.get("note", "")
    evidence = feat.get("evidence", "")

    description = note or (
        f"ISO/IEC 39075:2024 GQL feature — {title}. Status: {status}."
    )
    description = description.replace('"', "'").splitlines()[0][:200]

    fm = [
        "---",
        f'title: "{title}"',
        f'description: "{description}"',
        'status: "stable"',
        "generated: true",
        f'gql_feature_id: "{key}"',
    ]
    if since:
        fm.append(f'gql_since: "{since}"')
    if track:
        fm.append(f'gql_track: "{track}"')
    fm.append("---")

    body = [
        "",
        GENERATED_HEADER,
        "",
        f"# {title}",
        "",
        f"**Feature ID:** `{key}`  ",
        f"**Status:** {status_badge(status)}",
    ]
    phase = phase_label(since, conformance)
    if phase:
        body.append(f"**Since:** {phase}")
    if track:
        body.append(f"**Track:** {track}")
    if note:
        body += ["", "## Description", "", mdx_safe(note)]
    if evidence:
        body += ["", "## Evidence", "", f"`{evidence}`"]

    body += [
        "",
        "## Standards lineage",
        "",
        f"- ArcFlow implementation: `{conformance['implementation']}`",
        f"- Standard: {conformance['standard']} ({conformance['standard_version']})",
        f"- Conformance level: {conformance['conformance_level']}",
    ]

    body.append(provenance_footer(sync, "gql-conformance.json"))

    return "\n".join(fm) + "\n" + "\n".join(body)


# ---------------------------------------------------------------------------
# Extension pages (parsed from catalog markdown)
# ---------------------------------------------------------------------------

@dataclass
class ExtensionEntry:
    name: str       # "LIVE Queries"
    code: str       # "PAT-0022"
    slug: str       # "live-queries"
    body: str       # markdown body between heading and next ## or ---


HEADING_RE = re.compile(r"^## (.+?) \(([^)]+)\)\s*$", re.MULTILINE)


def parse_extensions(md: str) -> list[ExtensionEntry]:
    entries: list[ExtensionEntry] = []
    headings = list(HEADING_RE.finditer(md))
    for i, m in enumerate(headings):
        name = m.group(1).strip()
        code = m.group(2).strip()
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(md)
        body = md[start:end].strip()
        # Strip trailing --- separators (used between sections in catalog)
        body = re.sub(r"\n---\s*$", "", body).strip()
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        entries.append(ExtensionEntry(name=name, code=code, slug=slug, body=body))
    return entries


EVIDENCE_LINE_RE = re.compile(r"^\*\*Evidence:\*\*[^\n]*\n?", re.MULTILINE)
INLINE_CODE_REF_RE = re.compile(r"\s*\((?:PAT|I-INIT|EXT|ANTI|RAM|SPR|AFP|ARF)-[0-9A-Z]+\)")


def strip_internal_codes(text: str) -> str:
    """Remove internal initiative/pattern/wave codes from public-facing prose."""
    text = EVIDENCE_LINE_RE.sub("", text)
    # Drop parentheticals like "(PAT-0021)" inline in semantics descriptions.
    text = INLINE_CODE_REF_RE.sub("", text)
    # Tidy any double blank lines introduced by the strip.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def render_extension(ext: ExtensionEntry, conformance: dict, sync: dict) -> str:
    description = f"ArcFlow extension beyond ISO/IEC 39075 GQL — {ext.name}."
    fm = [
        "---",
        f'title: "{ext.name}"',
        f'description: "{description}"',
        'status: "stable"',
        "generated: true",
        "---",
    ]
    body = [
        "",
        GENERATED_HEADER,
        "",
        f"# {ext.name}",
        "",
        "**Type:** ArcFlow extension beyond GQL",
        "",
        strip_internal_codes(ext.body),
        "",
        "## Standards relationship",
        "",
        f"This is an extension to {conformance['standard']} ({conformance['standard_version']}). "
        "It does not affect the engine's conformance to the ISO standard — "
        "the extension surface is opt-in syntax that GQL leaves to implementations.",
    ]
    body.append(provenance_footer(sync, "arcflow-extensions-catalog.md"))
    return "\n".join(fm) + "\n" + "\n".join(body)


# ---------------------------------------------------------------------------
# Dashboard / TCK pages
# ---------------------------------------------------------------------------

def render_dashboard(conformance: dict, state: dict, extensions: list[ExtensionEntry], sync: dict) -> str:
    feats = conformance["features"]
    supported = sum(1 for f in feats.values() if f.get("status") == "SUPPORTED")
    unsupported = sum(1 for f in feats.values() if f.get("status") == "UNSUPPORTED")
    total = len(feats)
    tck_rate = state["tck_pass_rate"]

    fm = [
        "---",
        'title: "GQL Conformance"',
        f'description: "ArcFlow conformance to ISO/IEC 39075:2024 GQL — {supported}/{total} features supported, {tck_rate} openCypher TCK, {len(extensions)} extensions documented."',
        'status: "stable"',
        "generated: true",
        "---",
    ]

    body = [
        "",
        GENERATED_HEADER,
        "",
        "# GQL Conformance",
        "",
        f"ArcFlow implements **{conformance['standard']}** ({conformance['standard_version']}) at conformance level **{conformance['conformance_level']}**.",
        "",
        "## At a glance",
        "",
        "| Surface | Result | Detail |",
        "|---|---|---|",
        f"| openCypher TCK | **{state['tck_pass_rate']}** | release 2024.3, ~56% strict canonical |",
        f"| ISO GQL features | **{supported}/{total}** supported | {unsupported} unsupported (vendor choice) |",
        f"| ArcFlow extensions | **{len(extensions)} documented** | beyond-standard surface |",
        "",
        "## Vendor choices",
        "",
        "ISO GQL leaves several decisions to implementations. ArcFlow's:",
        "",
        "| Decision | Choice |",
        "|---|---|",
    ]
    for k, v in conformance.get("vendor_choices", {}).items():
        body.append(f"| `{k}` | `{v}` |")

    body += [
        "",
        "## GQLSTATUS codes",
        "",
        "Every query result carries a 5-digit GQLSTATUS code per the standard.",
        "",
        "| Code | Meaning |",
        "|---|---|",
    ]
    for code, meaning in conformance.get("gqlstatus_codes", {}).items():
        body.append(f"| `{code}` | {meaning.replace('_', ' ')} |")

    body += [
        "",
        "## Phases",
        "",
        "Conformance was achieved across these phases:",
        "",
        "| Phase | Name | Status |",
        "|---|---|---|",
    ]
    for pid, ph in conformance.get("phases", {}).items():
        body.append(f"| `{pid}` | {ph['name'].replace('_', ' ')} | {ph['status']} |")

    body += [
        "",
        "## Per-feature reference",
        "",
        "Every named feature in the conformance catalog has its own page under "
        "[`/reference/gql/`](/reference/gql/match-basic). The full list is in the sidebar.",
        "",
        "## Beyond GQL",
        "",
        f"ArcFlow ships {len(extensions)} documented extensions beyond the standard "
        "(live queries, Z-set incremental evaluation, evidence algebra, ASOF joins, "
        "GPU GraphBLAS, HNSW vector index, durable workflows, AI function namespace, "
        "and more). Each has its own page under "
        "[`/reference/extensions/`](/reference/extensions/live-queries).",
        "",
        "Extensions do not affect ISO conformance — they are opt-in syntax the "
        "standard explicitly leaves to implementations.",
        "",
        "## Test corpus",
        "",
        f"ArcFlow passes {state['tck_pass_rate']} openCypher TCK scenarios (~56% "
        "strict canonical, release 2024.3); hardening is in progress under I-INIT-GQLC. "
        "See [TCK Results](/reference/tck).",
    ]
    body.append(provenance_footer(sync, "gql-conformance.json"))
    return "\n".join(fm) + "\n" + "\n".join(body)


def render_tck(state: dict, sync: dict) -> str:
    pass_rate = state["tck_pass_rate"]
    completed = state.get("completed", [])
    fm = [
        "---",
        'title: "TCK Results"',
        f'description: "openCypher TCK pass rate: {pass_rate}. Generated from conformance/state.json on each engine release."',
        'status: "stable"',
        "generated: true",
        "---",
    ]
    body = [
        "",
        GENERATED_HEADER,
        "",
        "# openCypher TCK Results",
        "",
        f"**Pass rate:** `{pass_rate}` (openCypher TCK release 2024.3)  ",
        f"**Iteration:** `{state.get('iteration', 'n/a')}`  ",
        "**Conformance level:** Partial (measured) — hardening in progress under I-INIT-GQLC",
        "",
        "## What this means",
        "",
        f"ArcFlow passes **{pass_rate}** openCypher TCK scenarios at strict canonical "
        "equivalence (~56%, release 2024.3, measured 2026-06-29). Remaining scenarios fail "
        "on result values (~16%), error type/code (~11%), result shape (~8%), error phase "
        "(~7.5%), and ordering (~0.6%). Conformance hardening is in active progress under "
        "I-INIT-GQLC. The TCK is the industry-standard cross-vendor compatibility surface "
        "for Cypher.",
        "",
        "## Phases completed",
        "",
        "| Phase ID |",
        "|---|",
    ]
    for c in completed:
        body.append(f"| `{c}` |")
    body += [
        "",
        "## Reproducing",
        "",
        "The full per-scenario result set is too large to vendor in this repo "
        f"(one JSON per scenario, {pass_rate.split('/')[1]} files). To reproduce, "
        "run the conformance harness against your installed engine binary.",
    ]
    body.append(provenance_footer(sync, "conformance-state.json"))
    return "\n".join(fm) + "\n" + "\n".join(body)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def update_config_managed_sections(out_root: Path, conformance: dict, extensions: list) -> bool:
    """Add/replace the three generator-managed sections in docs/_config.json.

    Managed sections: 'gql-conformance', 'gql-features', 'arcflow-extensions'.
    All other sections are left exactly as-is. Section ordering is preserved
    if managed sections already exist; otherwise they are appended.
    """
    config_path = out_root / "docs" / "_config.json"
    cfg = json.loads(config_path.read_text())
    sections = cfg["sections"]

    # One top-level "GQL Reference" section with three drill-down child groups.
    # The query-language reference is one user intent; nesting it keeps the
    # top-level nav routed by intent rather than by generation source
    # (the three groups used to be three separate top-level sections).
    gql_reference = {
        "id": "gql-reference",
        "title": "GQL Reference",
        "managed": "scripts/generate-reference.py",
        "items": [
            {
                "title": "Conformance",
                "order": 1,
                "children": [
                    {"slug": "reference/gql-conformance", "title": "Conformance Dashboard", "order": 1},
                    {"slug": "reference/tck", "title": "openCypher TCK Results", "order": 2},
                ],
            },
            {
                "title": "Features",
                "order": 2,
                "children": [
                    {
                        "slug": f"reference/gql/{slugify_key(key)}",
                        "title": humanize_key(key),
                        "order": i + 1,
                    }
                    for i, key in enumerate(conformance["features"].keys())
                ],
            },
            {
                "title": "ArcFlow Extensions",
                "order": 3,
                "children": [
                    {
                        "slug": f"reference/extensions/{ext.slug}",
                        "title": ext.name,
                        "order": i + 1,
                    }
                    for i, ext in enumerate(extensions)
                ],
            },
        ],
    }

    # Remove the legacy top-level managed sections and any prior gql-reference,
    # then place the single nested section (preserving its slot if present).
    legacy_ids = {"gql-conformance", "gql-features", "arcflow-extensions"}
    new_sections = []
    inserted = False
    for s in sections:
        sid = s.get("id")
        if sid in legacy_ids or sid == "gql-reference":
            if not inserted:
                new_sections.append(gql_reference)
                inserted = True
            continue
        new_sections.append(s)
    if not inserted:
        new_sections.append(gql_reference)

    # Preserve sibling top-level keys (schema_version, lint, pinned_links, …);
    # only the `sections` array is generator-managed.
    cfg["sections"] = new_sections
    # ensure_ascii=False keeps raw UTF-8 (·, —, →) instead of \uXXXX escapes,
    # matching the hand-maintained config and the website's JSON consumer.
    new_text = json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"
    if config_path.read_text() == new_text:
        return False
    config_path.write_text(new_text)
    return True


def write_all(out_root: Path, data: dict) -> dict:
    """Write all generated files under out_root/docs/reference/. Returns counts."""
    conformance = data["conformance"]
    state = data["state"]
    sync = data["sync"]
    extensions = parse_extensions(data["extensions_md"])

    ref = out_root / "docs" / "reference"
    gql_dir = ref / "gql"
    ext_dir = ref / "extensions"
    gql_dir.mkdir(parents=True, exist_ok=True)
    ext_dir.mkdir(parents=True, exist_ok=True)

    written = {"gql": 0, "extensions": 0, "top": 0, "config": 0}

    for key, feat in conformance["features"].items():
        slug = slugify_key(key)
        if write_if_changed(gql_dir / f"{slug}.mdx", render_gql_feature(key, feat, conformance, sync)):
            written["gql"] += 1

    for ext in extensions:
        if write_if_changed(ext_dir / f"{ext.slug}.mdx", render_extension(ext, conformance, sync)):
            written["extensions"] += 1

    if write_if_changed(ref / "gql-conformance.mdx", render_dashboard(conformance, state, extensions, sync)):
        written["top"] += 1
    if write_if_changed(ref / "tck.mdx", render_tck(state, sync)):
        written["top"] += 1

    if update_config_managed_sections(out_root, conformance, extensions):
        written["config"] += 1

    return {
        **written,
        "feature_count": len(conformance["features"]),
        "extension_count": len(extensions),
    }


def check_mode(data: dict) -> int:
    """Regenerate into a temp tree and diff against the real tree."""
    with tempfile.TemporaryDirectory() as td:
        tmp_root = Path(td)
        # Mirror data/ + _config.json into tmp so write paths line up
        tmp_data = tmp_root / "docs" / "reference" / "data"
        tmp_data.mkdir(parents=True)
        for f in DATA.iterdir():
            if f.is_file():
                shutil.copy2(f, tmp_data / f.name)
        shutil.copy2(ROOT / "docs" / "_config.json", tmp_root / "docs" / "_config.json")

        write_all(tmp_root, data)

        # Diff every generated file (.mdx) and _config.json against the real tree
        drift: list[Path] = []
        for tmp_file in (tmp_root / "docs" / "reference").rglob("*.mdx"):
            rel = tmp_file.relative_to(tmp_root)
            real = ROOT / rel
            if not real.exists() or not filecmp.cmp(tmp_file, real, shallow=False):
                drift.append(rel)

        config_tmp = tmp_root / "docs" / "_config.json"
        config_real = ROOT / "docs" / "_config.json"
        if not filecmp.cmp(config_tmp, config_real, shallow=False):
            drift.append(Path("docs/_config.json"))

        if drift:
            print("Generated files are stale. Run scripts/generate-reference.py.", file=sys.stderr)
            for d in drift[:20]:
                print(f"  {d}", file=sys.stderr)
            if len(drift) > 20:
                print(f"  ... and {len(drift) - 20} more", file=sys.stderr)
            return 1
    print("Generated reference is up to date.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="CI mode: fail if generated files are stale")
    args = parser.parse_args()

    data = load_data()

    if args.check:
        return check_mode(data)

    counts = write_all(ROOT, data)
    print(
        f"Generated:\n"
        f"  {counts['feature_count']} GQL features in docs/reference/gql/ ({counts['gql']} updated)\n"
        f"  {counts['extension_count']} extensions in docs/reference/extensions/ ({counts['extensions']} updated)\n"
        f"  3 top-level pages ({counts['top']} updated)\n"
        f"  _config.json managed sections ({counts['config']} updated)\n"
        f"Synced at: {data['sync'].get('synced_at', 'unknown')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
