# Release Manifest Consumer (docs slice of arcflow I-INIT-0116)

This document records the **documentation-domain slice** of the cross-repo
initiative `I-INIT-0116 — Release Artifact Manifest & Customer Embedding Path`
authored in the engine repo at
`arcflow/kanban/roadmap/initiatives/I-INIT-0116-Release-Artifact-Manifest.md`.

The full plan — including the engine domain's manifest authoring (Stream B) and
the marketing domain's consumer rewrite — lives in arcflow. This file tracks the
docs-domain slice and the contract this repo has with the manifest.

---

## NOTE(invariant): Write docs for what the manifest says exists.

The existing invariant from `sdk-surface-docs.md` extends here:

> Write docs for what exists. Never describe unimplemented APIs.

The manifest is the operational definition of "what exists." Once consumer
wiring lands (RAM-B3 in arcflow's I-INIT-0116), every install command in this
repo's MDX, README, and agent-context files is rendered from
`release-matrix.json`. Hand-written install commands anywhere in `docs/`,
`install/`, `llms.txt`, or `llms-full.txt` are a CI failure.

If the manifest says `pip install arcflow` is `status: planned`, this repo
shows it as a planned artifact with target quarter — never as a working command.
If a contributor wants to add a `pip install` line, the path is: ship the wheel
(arcflow repo), flip the manifest entry to `shipped`, and the next build picks
it up automatically.

---

## Why This Repo Exists in the SSoT Story

Three bounded contexts share one kernel:

- **Engine domain** (`arcflow/`, closed) — authors `RELEASE-MATRIX.toml`,
  publishes `release-matrix.json` as a GitHub Release asset on every release.
- **Documentation domain** (`arcflow-docs/`, this repo, public MIT) — public
  developer-facing docs, cookbooks, examples. Consumes the manifest.
- **Marketing/web domain** (`oz-platform/apps/cloud/website/`) — public
  landing, install button, agent prompt. Consumes the manifest.

This repo is a **read-only consumer**. It does not author install state.
It does not override or extend manifest entries locally.

---

## What This Repo Owns

| Surface | Current shape | Post-RAM-B3 shape |
|---|---|---|
| `docs/installation.mdx` | Hand-rolled npm matrix | `<InstallMatrix />` reads manifest |
| `docs/bindings.mdx` lines 17-22 | Hand-rolled curl/pip/npm/docker | `<InstallMatrix />` reads manifest |
| `install/README.md` | Hand-rolled install method table (line 57+) | `<InstallMatrix />` reads manifest |
| `install/install.sh` | Canonical installer source — owns the asset | Unchanged content; `Usage:` header URL updated to `/install/arcflow` |
| `llms.txt` | Hand-written agent context | Build-time generated from manifest template |
| `llms-full.txt` | Hand-written full agent context | Build-time generated from manifest template |
| `typescript/package.json` | Local SDK source for `arcflow` npm package | Unchanged authoring; `version` flips with engine release; manifest `node` entry tracks publish status |

The `<InstallMatrix />` component is the only allowed renderer of install
commands. Wiring lands in RAM-B3 (engine I-INIT-0116).

---

## What This Repo Does NOT Own

- The manifest itself (`RELEASE-MATRIX.toml`) — lives in arcflow.
- Authoring install state — engine domain only.
- The `/install` URL the marketing site exposes — that's `oz-platform`'s job
  (it deploys this repo's `install/install.sh` via build-time copy or rewrite,
  but does not edit it).
- The agent-prompt component on the marketing site — that's `oz-platform`'s
  surface; it has its own consumer wiring (RAM-B4 + PAT-WEB-0003).

---

## Linked External Patterns

This repo does not maintain a local pattern catalog (it is a docs/SDK repo, not
an engine repo). The patterns governing this consumer slice are authored in the
engine repo:

- `arcflow/kanban/patterns/PAT-0042-Release-Artifact-Manifest.md` — manifest as SSoT
- `arcflow/kanban/patterns/PAT-0043-Manifest-Driven-Install-Disclosure.md` — consumer contract (this repo + oz-platform both governed by it)
- `arcflow/kanban/patterns/ANTI-0022-Aspirational-Install-Documentation.md` — what we are no longer allowed to do

The marketing repo authors its own local patterns:

- `oz-platform/apps/cloud/website/kanban/patterns/PAT-WEB-0003-Install-Surface-Reads-From-Engine-Manifest.md`
- `oz-platform/apps/cloud/website/kanban/patterns/ANTI-WEB-0002-Vercel-Project-URL-Disclosure.md`

---

## Build-Time Manifest Fetch — Operational Contract

When RAM-B3 lands:

- `<InstallMatrix />` fetches `https://github.com/ozinc/arcflow/releases/latest/download/release-matrix.json`
  at build time.
- Schema is `schema_version: 1`. Unknown major versions are rejected (build fails).
- Build fails if the fetch fails. **No fallback to a baked-in last-known-good
  manifest.** No partial render. No prose substitute. (PAT-0042 invariant.)
- The manifest fetch is cached for the build duration; it is not a hot-path
  runtime fetch.

---

## CI Lint Rule

After RAM-B3:

```text
forbidden in docs/, install/, *.txt (outside <InstallMatrix /> output):
  /pip install arcflow/
  /npm install arcflow/
  /cargo add arcflow/
  /cargo install arcflow/
  /ghcr\.io\/[^\/]+\/arcflow/
  /\/install_arcflow/
```

If any of these literal strings appear in this repo, CI fails.

---

## Sibling: Cookbook Consumer Contract

This repo has *two* manifest consumer contracts:

- **Install consumer** (this document, governed by PAT-0043 in arcflow) —
  surfaces install state in MDX/text via `<InstallMatrix />`.
- **Recipe consumer** (`planning/cookbook-strategy.md`, governed by PAT-0044
  in arcflow) — uses shipped APIs in runnable cookbook examples.

Both consumers read the same kernel (`release-matrix.json`). Neither authors
it. The two contracts compose: a recipe linking to install instructions
references the install consumer's output; an install matrix linking to
example recipes references the recipe consumer's index. No content
duplication between them — both render from the manifest.

## Resume Point for the Customer

The customer (football-transformer NGS world model) is blocked on this
initiative. Their unblock path runs in parallel as **Stream A** in
`arcflow/kanban/roadmap/initiatives/I-INIT-0116-Release-Artifact-Manifest.md`:

- RAM-A1: marketing-site typo + lying-line strip (oz-platform).
- RAM-A2: asset path migration to `/install/arcflow` (oz-platform + this repo).
- RAM-A3: hand-delivered Python wheel from the engine repo.
- RAM-A4: seed cookbook recipe `temporal-spatial-parquet-ingest/` (this repo,
  per `planning/cookbook-strategy.md`) — covers the customer's exact data
  shape (large batch temporal + spatial Parquet ingestion, NFL NGS player
  tracking, DuckDB-like batch). The recipe seeds the structural template
  that I-INIT-0117 makes sustained.

This repo's `install/install.sh` is the canonical installer; its `Usage:`
header URL is updated in RAM-A2 to match the new asset path.
