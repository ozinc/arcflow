# Contributing to ArcFlow Docs

Thanks for working on ArcFlow's documentation. This file is the contract — what
pages exist, where they belong, who edits them, and how the docs repo stays
honest as the engine ships.

## TL;DR

```sh
# Validate before you push
scripts/check-docs-structure.py        # structural integrity (registration, no duplicates)
scripts/generate-reference.py --check  # generated reference pages match upstream data
```

If both pass, your PR is structurally sound. The rest of this document explains
why those checks exist and where each kind of edit belongs.

## The two layers

The docs repo is structured as **two distinct layers** that follow different
editing rules:

| Layer | What it is | Editing model | Lives in |
|---|---|---|---|
| **Domain concepts** | Durable knowledge — mental model, decision rules, when-to-use, when-not-to-use, failure modes | Hand-authored, refined over time, owned by humans | `concepts/`, `guides/`, `tutorials/`, `recipes/`, `use-cases/`, top-level capability pages, `worldcypher/` syntax pages |
| **Reference / intake** | Machine-derived facts — feature lists, conformance status, syntax specs, error codes | Generated from upstream engine data, **never hand-edited** | `reference/gql/`, `reference/extensions/`, `reference/gql-conformance.mdx`, `reference/tck.mdx`, `reference/extensions-regressions.mdx` |

The reader doesn't see the split — they follow a clean Learn → Build → Reference
path through the sidebar. Contributors *do* see the split, because it dictates
where edits go.

**Why the split matters:** the engine ships often. Hand-authoring 60+
per-feature pages and 13 extension pages would rot the day after each release.
Generating them keeps facts in sync; hand-authoring concepts keeps depth real.

## Where does my edit belong?

```
Need to fix a typo or sharpen prose?
├── In a page with `generated: true` frontmatter? → STOP. Edit the upstream
│   data in docs/reference/data/ (and probably the engine repo). Regenerate.
└── Otherwise → edit the .mdx directly.

Adding new content?
├── New mental-model concept (a "way of thinking")? → docs/concepts/
├── New how-to ("here's how to accomplish X")? → docs/guides/
├── New step-by-step learning path? → docs/tutorials/
├── New copy-paste pattern? → docs/recipes/
├── New customer-facing application? → docs/use-cases/
├── New top-level capability the engine just shipped? → docs/{slug}.mdx
├── New GQL syntax page? → docs/worldcypher/
├── New CLI/server/deployment page? → docs/cli/, docs/server/, docs/deployment/
└── New machine-derived reference data? → DON'T add MDX. Add data upstream
    in the engine repo, re-run scripts/sync-conformance-data.sh, then
    scripts/generate-reference.py.

Removing or renaming a page?
└── Read the "Retiring a page" section below before deleting.
```

After adding a page, **register it in `docs/_config.json`** under the
appropriate section. The structure linter (`check-docs-structure.py`) will
fail your PR if you forget.

## Frontmatter contract

Every `.mdx` file starts with YAML frontmatter:

```yaml
---
title: "Page Title"
description: "One-line description that appears in search results and link previews."
section: "section-id"          # must match a section.id in _config.json
status: "stable"               # stable | beta | deprecated
---
```

Generated pages add:

```yaml
generated: true                # MUST be present on every page under
                               # docs/reference/gql/ or docs/reference/extensions/
                               # MUST NOT appear anywhere else
```

## The compounding rule

When you add a page, you owe an answer to **"what does this replace, deepen, or
sit beside?"**

- **Replace** an existing page when the new one covers the same idea more
  precisely. Delete or redirect the old page in the same PR.
- **Deepen** an existing page when the new content sharpens triggers,
  boundaries, or failure modes. Edit in place rather than creating a parallel
  page.
- **Sit beside** when the new page introduces a genuinely separate bounded
  context. Add cross-links in both directions.

If you can't answer the question, don't merge yet. Two pages saying nearly the
same thing is the most common drift mode.

## Maturity bar for hand-written pages

A page that just labels and explains is M1. Aim for M3+:

- **M1 (label):** Concept has a name and a paragraph of explanation.
- **M2 (heuristic):** Tells the reader what to do or avoid.
- **M3 (operating rule):** Includes triggers, boundaries, failure modes, and
  output implications. Reader can apply the concept *and* know when not to.
- **M4 (connected model):** Explicitly links to adjacent concepts and surfaces
  contradictions or tradeoffs.

Concepts pages should reach M3 before merging. The linter doesn't enforce
maturity automatically (yet) — it's a review gate.

## Retiring a page

A common mistake: adding a new page without retiring the old one it supersedes.
The repo accumulates fragments and the sidebar gets noisier each release.

**Before deleting:**

1. Note every place the old page is linked (`grep -r "old-slug" docs/`).
2. Decide: redirect the URL, or migrate the content into a sibling page?
3. Update inbound links in the same PR.
4. Remove the slug from `docs/_config.json`.

**Never** leave an orphan: a `.mdx` file that's not in `_config.json`. The
linter will flag it. Either register it or delete it.

## Generated content — the rules

Pages under `docs/reference/gql/`, `docs/reference/extensions/`, and the three
top-level pages (`gql-conformance.mdx`, `tck.mdx`,
`extensions-regressions.mdx`) are **regenerated from upstream engine data on
every engine release**.

- Source data: `docs/reference/data/` (vendored from the engine repo)
- Generator: `scripts/generate-reference.py`
- Sync script (maintainer-only): `scripts/sync-conformance-data.sh`
- CI check: `scripts/generate-reference.py --check` (regen + diff)

**Hand-edits to generated pages will be silently overwritten** the next time
the generator runs. The provenance footer at the bottom of each page tells
readers where the source data lives.

To improve a generated page, you have three options:

1. **Improve upstream data** in the engine repo's
   `docs/conformance/gql-conformance.json` or
   `arcflow-extensions-catalog.md`, then re-sync.
2. **Improve the generator template** in `scripts/generate-reference.py` to
   render existing data more usefully.
3. **Add a "See also" hand-written page** in `docs/concepts/` or
   `docs/guides/` and link to it. The generated page provides the spec; the
   hand-written page provides the depth.

## What NOT to do

- Don't add a `.mdx` without registering it in `_config.json`.
- Don't hand-edit pages with `generated: true` frontmatter.
- Don't add `generated: true` to a hand-written page (the linter rejects this).
- Don't bypass `--no-verify` to skip the linter — fix the underlying issue.
- Don't commit the same idea in two pages because you weren't sure where it
  belonged. Pick one home and cross-link.
- Don't document an unshipped engine feature. Only ship docs for what
  the current engine release actually supports.

## Repo boundary (important)

This repo is the **developer surface** — docs, TypeScript SDK, MCP package,
React hooks. The Rust engine lives in a separate repo (`arcflow/`). Full
governance is in [`REPO-SPLIT.md`](../REPO-SPLIT.md).

If you find yourself wanting to write Rust source, edit a `crates/` directory,
or document an unreleased feature: stop. That work belongs in the engine repo.

## Filing issues

Use the GitHub issue tracker. Common categories:

- **Typo / wording** — fastest path is a PR; we'll merge.
- **Missing page** — open an issue describing what's missing and where it
  should live (concept? guide? reference?).
- **Broken example** — open an issue with the exact query and the error.
- **Doc claims feature that isn't shipped** — high priority. Tag with
  `unshipped-feature`.
- **Generated page is wrong** — point at the upstream data file, not the MDX.

## Final note

The structure of this repo is the structure of how ArcFlow is taught. Treat
edits as a chance to compound the model — each page slightly sharper than
before — not as a chance to add another fragment. If your PR makes the docs
better at making decisions, ship it. If it just makes them larger, groom first.
