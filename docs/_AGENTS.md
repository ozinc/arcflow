# arcflow-docs/docs/ — IA contract

The IA shape is Object-First: top-level sections answer *"what kind of thing
is this page?"* — concept, clause, capability, operation, reference, use-case,
walkthrough, first-use. Multi-level nav supported via nested `children`.
Lint-enforced (R1..R9).

Cross-repo SSoT map: `oz-platform/apps/cloud/website/kanban/CROSS-REPO-MAP.md`.

## Rules

| ID | Rule | Lint check |
|----|------|------------|
| R1 | A reader reaches the right page in ≤3 clicks + ≤5 s scanning | Manual blind test on releases |
| R2 | Top-level sections answer one question: *what kind of thing is this?* | `section_kind_map` in `_config.json` |
| R3 | Top level capped at `lint.max_top_level_sections` (default 8) | `_config.json` validator |
| R4 | Lint runs on every PR | CI pre-commit (`scripts/check-docs-structure.py`) |
| R5 | Each documentable concept has exactly one canonical page; others declare `canonical: <slug>`. Registered (non-facet) pages **must** declare `kind:` matching the section's declared kind | CI: presence + match check |
| R6 | `/llms.txt` canonical-page count ≥ pre-change baseline — agent vocab does not shrink | CI: diff llms.txt enumeration |
| R7 | Frontmatter is config-deprecated for placement/ordering — neither `section:` nor `order:` may appear. `_config.json` is the sole SSoT | CI: fails on either field |
| R8 | Sibling items inside a parent have unique `order:` values | CI: order collision check |
| R9 | `_config.json` carries `schema_version: "v2"` | CI |

## Sections (kind enum)

| Section | Kind | Purpose |
|---------|------|---------|
| Start | `first-use` | Quickstart, install, language bindings |
| Concepts | `concept` | Mental models — world model, evidence model, sync, persistence |
| WorldCypher | `clause` | Query-language reference — clauses, composition, functions |
| Capabilities | `capability` | Engine features — live queries, vector, RAG, agent stack |
| Operations | `operation` | Run-in-prod artefacts — CLI, server, deployment, architecture |
| Reference | `reference` | Dictionary — API, types, errors, glossary, compat, licensing |

## Sibling surfaces (NOT in `/docs/*`)

- `/spec/gql/{conformance,features,extensions}` — GQL standard conformance dashboards (76 generated stubs lifted out of `/docs/reference/gql/*` + `/docs/reference/extensions/*` + `/docs/reference/{gql-conformance,tck,extensions-regressions}`)
- `/arcflow/cookbooks` — runnable recipes (oz.com marketing surface; `/docs/cookbooks-index` is removed)
- `/engine` — interactive REPL (pinned in docs sidebar header)

## Frontmatter contract

```yaml
---
title: "Page Title"
description: "One-line meta description"
kind: concept | clause | capability | operation | reference | first-use   # REQUIRED — must match section kind
order: number                                                              # within parent group
canonical: <other-slug>                                                    # OPTIONAL — declare this page is a facet
concepts: [list, of, concept, tags]                                        # for R5 lint
since: "1.0.0"                                                             # OPTIONAL
status: stable | beta | deprecated                                         # OPTIONAL
---
```

**Deprecated** (do not use; deleted at restructure time): `section:` (config is now sole SSOT).

## Boundary case ledger

Four pages have rubric-ambiguous placement. The ledger fixes the call so future PRs don't re-litigate:

- **`event-sourcing`** → Capabilities. Rubric: capability with concept facets (concepts/persistence, concepts/snapshots) pinned underneath.
- **`agent-native`** → Capabilities. Rubric: philosophy IS the capability — manifesto framing is the brand promise of this capability, not a separate kind.
- **`sync`** → Capabilities. Rubric: capability is canonical; operations/architecture/sync-protocol is a facet attached to the canonical, not a sibling.
- **`architecture`** → Operations/Architecture/Engine. Rubric: architecture is an operational artefact (how to tune/run the engine); cloud-architecture and sync-protocol live alongside as siblings under Operations/Architecture.

## How to add a new doc page

1. Choose the right section per *kind* (see table above).
2. Add MDX file at the slug path implied by your section + sub-group.
3. Add the entry to `_config.json` under the right section/group.
4. Set `kind:` frontmatter to match section's kind.
5. If the concept already has a canonical page elsewhere, set `canonical: <slug>` instead of adding a new sidebar entry.
6. CI lint will catch order collisions, missing canonicals, kind mismatches.

**Adding a new top-level section requires a planning dossier review** — `_config.json` validator does not allow PRs to push past `max_top_level_sections`.
