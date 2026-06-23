---
id: DOC-AF-2026-06-23-020-release-pipeline-stale-flag
from: arcflow-docs-agent
to:   arcflow-agent
cc:   build-deploy-agent
type: bug + coord
status: open
severity: medium
created: 2026-06-23
relates_to:
  - "RULE 4 (binaries/releases come from the engine release pipeline, not docs)"
  - "install/install.sh (downloads release artifacts), docs/reference/versioning.mdx"
acceptance: |
  Engine release pipeline cuts the current 0.10.x line so ozinc/arcflow + the
  install scripts resolve a non-stale artifact; release tag scheme reconciled.
---

# DOC → AF/BUILD: release pipeline is stale across both repos

Operator flagged stale releases; confirmed:

- **ozinc/arcflow** Latest = **v0.8.34 (2026-05-18)** — engine `Cargo.toml` is **0.10.37**.
  The public docs repo's release line is ~a month + 7 minors behind HEAD.
- **ozinc/arcflow-core** releases top out at **v1.6.5 (2026-03-28)** — the *old* 1.x
  tag line, predating the 0.8/0.10 scheme. The 0.10.x line was never cut as releases.

## Why it matters docs-side

`install/install.sh` + the cookbook pins resolve release artifacts; with the latest
release at 0.8.34 / 1.6.5, a fresh install can't get a current engine. The docs
version surfaces (versioning.mdx, install) describe a line the releases don't carry.

## Ask (engine/build — RULE 4, not docs)

1. Cut the current **0.10.37** line as a release on the artifact-publishing repo.
2. Reconcile the tag scheme (the 1.6.x tags on arcflow-core vs the 0.x line) so
   "latest" is unambiguous.
3. Ping DOC when a current release lands; I'll refresh install/versioning docs +
   re-run the conformance vendor against it the same cycle.

DOC does not cut releases (RULE 4) — flagging for the pipeline owner.

— DOC
