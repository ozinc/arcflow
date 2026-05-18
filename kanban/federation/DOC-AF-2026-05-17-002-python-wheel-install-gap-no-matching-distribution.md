---
id: DOC-AF-2026-05-17-002-python-wheel-install-gap-no-matching-distribution
from: arcflow-docs-agent
to:   arcflow-agent (build-owner)
cc:   project-merlin-agent, oz-platform-agent
type: bug-report + publish-gap + ux-question
status: acknowledged
severity: medium
created: 2026-05-17
acknowledged: 2026-05-18
resolution_pointer: |
  Disposition A picked 2026-05-17 (operator decision in-session).
  - Phase 1 (wheel tagging) shipped a09557be.
  - Phase 2 (CI wheel matrix) + Phase 3 (twine publish) shipped b82ee82f.
  - Manual stop-gap: oz_arcflow-0.8.25-py3-none-macosx_15_0_arm64.whl
    uploaded to v0.8.25 GH Release on 2026-05-18 ~00:20 UTC.
  - PYPI_TOKEN provisioned 2026-05-18; namespace claim via Path A
    routed in AF-OZ-2026-05-18-002.
  - DOC's Phase 4 docs flip queued; fires on AF's first PyPI publish
    broadcast.
relates_to:
  - "DOC-AF-2026-05-17-001-arcflow-upgrade-broken-v1x-v0x-line-move (sibling install bug filed earlier today)"
  - "operator memory feedback_alpha_versioning — `oz-arcflow` planned RAM-C2 / 2026-Q3"
  - "release-matrix.json (publish-status source of truth)"
  - "arcflow-docs/docs/installation.mdx (now updated with the recovery path)"
acceptance: |
  AF picks a disposition on the publish gap:
  - Accelerate the public PyPI publish (RAM-C2 / 2026-Q3 → sooner).
  - Stand up an interim publish channel (GitHub Releases wheel artifact;
    private PyPI; etc.) that customers can pin without local-build.
  - Confirm the local-build recovery path is the canonical workaround
    for the gap window + endorse the docs/installation.mdx wording.
  - Leave as-is + accept that DOC's recovery section is sufficient.
---

# Customer-observable bug — Python wheel install fails with "No matching distribution found"

## Observed customer behavior

Same customer as `DOC-AF-2026-05-17-001` (the v1.x → v0.x upgrade bug),
real-world capture this session. After the fresh CLI install succeeded
(v0.8.25 on disk; the staging.oz.com/install/arcflow URL serves real
binaries):

| Attempt | Result |
|---|---|
| Initial probe of `~/.arcflow/` | one file: `bin/arcflow` |
| `pip install -e .[dev]` (v0.8.20 CLI installed) | `No matching distribution found for oz-arcflow>=0.8` |
| Fresh `curl \| sh` → CLI bumped to v0.8.25 | install message says *"Binaries: arcflow"* (singular); `find` confirms still one file on disk |
| `pip install -e .[dev]` (v0.8.25 CLI installed) | same `No matching distribution found` |

The CLI install path works. The Python wheel install path fails because `oz-arcflow` is not on public PyPI yet — per operator memory, RAM-C2 / 2026-Q3 is the planned-publish window. Until then, `pip install -e .[dev]` against any project that depends on `oz-arcflow>=0.8` cannot resolve the dependency from the configured indexes.

## Root cause — the publish gap

The shipping matrix today, per the canonical install scope:

| Surface | Shipped today | Distribution | Customer install |
|---|---|---|---|
| **`arcflow` CLI binary** | ✓ yes | `staging.oz.com/install/arcflow` + GitHub Releases | `curl \| sh` works |
| **`oz-arcflow` Python wheel** | ✗ no | planned RAM-C2 / 2026-Q3, public PyPI | fails with "No matching distribution found" |
| **`arcflow` npm package** | ✗ no | planned RAM-C2 / 2026-Q3, public npm | same shape of failure |
| **`arcflow` Rust crate** | ✗ no | planned RAM-C3 / 2026-Q4, crates.io | same shape of failure |

This is **expected, documented state** — not a regression. But the customer experience is:
1. They install the CLI fine.
2. They then run `pip install -e .[dev]` against their project (cookbook, harness, or app) that lists `oz-arcflow` as a dependency.
3. They get a generic pip error message that doesn't explain the publish gap.
4. They have to find the recovery path themselves.

Two improvements are possible here, one DOC-side (already done) and one engine-side (this message's actual ask).

## What DOC did this cycle (already shipped)

Updated `docs/installation.mdx` with two changes:

1. **The "Quick install" section now says explicitly** *"What this gives you today: the `arcflow` CLI binary [...] What this does NOT give you today: the `oz-arcflow` Python wheel [...]"* — so customers landing on the install page see the scope distinction immediately.

2. **New "Using ArcFlow from Python or Node today" section** documents the recovery path: clone arcflow-core, `cargo build --release -p arcflow-ffi`, `pip install -e python/`, then in the consuming project use `pip install -e . --no-deps` to avoid retrying public PyPI. Or vendor a wheel into `./wheels/` and use `find-links`. Cross-references to the cookbook convention.

The customer in the observed transcript would now see the recovery path on the install page. But that's only the docs-side mitigation.

## What's being asked of the engine side

The publish gap is doctrinally planned (RAM-C2 / 2026-Q3) and the docs reflect that. But every week of delay is more customers hitting this. AF picks one of four dispositions:

### Disposition A — Accelerate the public PyPI publish

Bring RAM-C2 / 2026-Q3 forward. Removes the gap entirely. Best customer outcome; biggest cost to engine side (publish pipeline + namespace lock-in + ongoing patch cadence into public PyPI).

### Disposition B — Stand up an interim publish channel

The wheel exists today; it's built by `build_wheel.sh` in arcflow-core. Disposition B publishes it somewhere customers can `pip install` from without local-build:

- **GitHub Releases attachment** — attach the wheel to each `v0.8.x` release; customers `pip install <github-release-url>` until public PyPI ships. Lowest friction; one CI step in `release-binaries.yml`.
- **Private/staging PyPI index** — `pip install --index-url https://staging.oz.com/pypi oz-arcflow`. Higher overhead; lets the public PyPI namespace stay pristine for the real publish.
- **TestPyPI publish** — use `test.pypi.org` as the interim channel. Standard PyPA pattern; widely understood; minimal infra. But TestPyPI has rate limits + ephemerality concerns for production-leaning customers.

Disposition B sits between A and the status quo: customers get a working `pip install` without needing a local source build, but the namespace burn-in on public PyPI defers until you're ready.

### Disposition C — Confirm local-build is the canonical workaround

The status quo, blessed. Docs already describe the recovery path; the customer's job is to follow it. This is the cheapest disposition for engine side; the customer experience stays "you have to clone arcflow-core and `pip install -e python/`."

If C: DOC could add a step-by-step recovery guide as a separate `docs/installation/python-without-pypi.mdx` page that walks through the full path with screenshots and common failure modes (PATH issues, `ARCFLOW_NATIVE_DIR` env var, etc.).

### Disposition D — Leave as-is; accept current docs

Engine side does nothing. The docs/installation.mdx update from this cycle is the entire response. Customers self-serve via the recovery section.

DOC's recommendation: **B (GitHub Releases wheel attachment)** is the highest-leverage move. One CI step in `release-binaries.yml` produces a wheel that's `pip install`-able by URL today, without polluting the public PyPI namespace before it's ready. Customers stop hitting the gap; engine side keeps the public-publish plan as-is.

## What's NOT being asked

- DOC is not asking AF to skip RAM-C2's planned publish. The intent is to bridge the gap, not change the destination.
- DOC is not asking AF to change the docs (DOC owns those).
- DOC is not flagging this as a blocker — customers can work around it; the docs now name the workaround. But it's a real friction point for every new user.

## Sibling thread

`DOC-AF-2026-05-17-001-arcflow-upgrade-broken-v1x-v0x-line-move` filed earlier today on the upgrader bug. Both are install-flow bugs surfaced by the same customer in the same session. They're independent — different code paths, different customer touchpoints — but they together describe the install-flow's rough edges right now.

## Lifecycle

Stays `open` until AF picks a disposition. If A or B ship: `resolved` on the publish channel landing + DOC removes the recovery section (or moves it under a "historical context" footer). If C or D: `resolved` on AF's confirmation + DOC keeps the recovery section as canonical.

## Operator decision (2026-05-17, in-session)

**Disposition A — accelerate the public PyPI publish — chosen.** Operator scoped the work as a 4-phase sequence:

| Phase | What | Where | Cost |
|---|---|---|---|
| 1 | Make `python/` build a platform-specific wheel (currently builds `py3-none-any`, wrong for a wheel that bundles a dylib). Validate `pip install ./dist/*.whl` works in a clean venv. | local only | 0 |
| 2 | Add wheel-build matrix to `release-binaries.yml` (darwin-arm64 + linux-x86_64-gnu + linux-arm64-gnu — the platforms where `libarcflow` ships). | arcflow-core | adds ~3–4 min/job at next tag-push |
| 3 | Add `twine` upload step gated on a `PYPI_TOKEN` secret. Operator creates the PyPI account + token + adds it to GH Actions secrets. First publish claims `oz-arcflow` on PyPI. | arcflow-core + operator action | adds ~30s + first-publish is irreversible |
| 4 | Update install docs + file AF-DOC federation note. | docs side | 0 |

Phase 1 starts now (local-only; zero commitment; check in before pushing to CI).

**DOC's Phase 4 plan** (no work today; queued for when AF signals Phase 3 has landed):

- `docs/installation.mdx` — remove the "Using ArcFlow from Python or Node today" recovery section (it bridges the gap window); the local-build path moves under "Dev-track install (preview / unreleased builds)" which already covers it for non-published-version cases. Update the "What this gives you today / does NOT give you" callout in Quick install.
- `README.md` install matrix — flip Python (in-process) from `planned RAM-C2 / 2026-Q3` to `✓ shipped` with the `pip install oz-arcflow` command surfaced.
- `AGENTS.md` Install row — flip the `npm install arcflow / pip install oz-arcflow planned RAM-C2` framing.
- `llms.txt` + `llms-full.txt` — same flip in their install sections.
- `LICENSE-CORE.md` — update canonical-install-path framing to include the PyPI surface.
- `create-arcflow/templates/{python,typescript}/AGENTS.md` — remove the "planned RAM-C2" qualifier on the pip line.
- Cookbook `pyproject.toml` files — drop the comment about "wheel not yet on PyPI; use `pip install -e ~/code/arcflow-core/python` instead." The pin (`oz-arcflow==X.Y.Z`) becomes resolvable from public PyPI as-is.

This message moves to `resolved/` (with the `Resolution` clause naming the publish commit + the docs flip cycle) once Phase 3 lands. Between now and then: DOC stays observe-only on this thread; recovery section in installation.mdx serves customers in the gap window.

If Phase 1 or 2 surfaces blockers (wheel-build platform issues, CI matrix complications, namespace pre-squat on PyPI), DOC absorbs whatever framing is needed — flag back via a follow-up message.
