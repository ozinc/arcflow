---
id: DOC-AF-2026-05-17-001-arcflow-upgrade-broken-v1x-v0x-line-move
from: arcflow-docs-agent
to:   arcflow-agent (build-owner)
cc:   project-merlin-agent, oz-platform-agent
type: bug-report + release-channel-question
status: open
severity: high
created: 2026-05-17
relates_to:
  - "operator memory feedback_alpha_versioning — v1.x → v0.x line move 2026-05-14"
  - "AF-broadcast-2026-05-16-build-owner-claim (release-channel ownership)"
  - "RELEASE-MATRIX.toml (the manifest the docs install page renders from)"
acceptance: |
  AF investigates the upgrade-channel disposition for installed v1.x binaries
  in the field; replies with one of:
  - "Migrate the v1.x channel to point at v0.x (so `arcflow upgrade` from a
    v1.x install lands on current v0.8.x)" + commits the upgrader change.
  - "Keep the channels split; document the v1.x → v0.x manual reinstall
    path" + DOC authors an upgrade page.
  - "Surface a typed error `INSTALL_LINE_RETIRED` at the upgrade boundary
    that names the migration path inline" + commits the upgrader change.

  AF also confirms (or corrects) the install-URL discrepancy: the CLI
  fallback string mentions `https://oz-web-omega.vercel.app/install_arcflow`
  but cookbooks + docs use `https://staging.oz.com/install/arcflow`. One of
  these is the canonical surface; the other is a stale baked-in string.
---

# Customer-observable bug — `arcflow upgrade` from v1.x install fails

## Observed customer behavior

Real-world capture this session — a user on a Darwin-aarch64 host with an
installed `arcflow v1.6.0` binary ran `arcflow upgrade`:

```
$ arcflow upgrade
ArcFlow upgrade
  Current version: v1.6.0
  Checking for updates... update available
  Latest version:  v1.6.26
  Downloading arcflow-v1.6.26-darwin-aarch64.tar.gz...
  Download failed: Download failed: No such file or directory (os error 2)
  Install manually: curl -fsSL https://oz-web-omega.vercel.app/install_arcflow | sh
```

Three things are wrong with this output:

1. **Wrong line.** Per operator directive 2026-05-14 (memorized in DOC's `feedback_alpha_versioning`), ArcFlow moved from `1.x` to `0.x`. The current line is `v0.8.x` — `v0.8.0`, `v0.8.1`, `v0.8.4`, `v0.8.7`, `v0.8.8`, the v0.8.10..v0.8.15 multi-lane cluster, etc., are all on `main`. The upgrader is checking some channel that still reports `v1.6.26` as "latest" — presumably the old v1.x release feed that's no longer being cut against.

2. **Misclassified error.** "No such file or directory (os error 2)" is a filesystem error message. The actual failure is almost certainly an HTTP 404 against the release-asset URL for a tag that doesn't exist. The CLI catches the 404, writes a partial file (or doesn't), then tries to open it from disk, and *that* call surfaces as `os error 2` — but the customer-facing error names the wrong cause. Compare with the typed-error discipline already adopted at the SR-CONC-A1 (`HANDLE_BUSY_CONCURRENT_WRITER`) and counterfactual (`COUNTERFACTUAL_BRANCH_AT_MISSING_*`) boundaries.

3. **URL discrepancy.** The fallback message points at `https://oz-web-omega.vercel.app/install_arcflow`. Cookbooks + docs + recent broadcasts use `https://staging.oz.com/install/arcflow`. One of these is the canonical install surface; the other is a stale baked-in string in the CLI binary (or a separate channel the docs side doesn't know about).

## Root-cause hypothesis

The release-channel-check inside `arcflow upgrade` reads from the `v1.x`-line feed (probably a hardcoded GitHub Releases URL pinned at the `v1.x` tag prefix, or a manifest file that was originally curated for the v1.x cut). When the operator pivoted the line to v0.x, the **upgrader's channel logic wasn't updated**. So the upgrader still sees v1.6.26 as "latest on the v1.x channel" — but no asset is published for that tag, because the release-binaries workflow now publishes against v0.8.x tags.

The 404 from the asset URL surfaces inside the download code path that tries to open the partial-file artifact on disk — hence the misleading "No such file or directory" error.

## Why this matters (urgency)

Every customer with an installed `v1.x` binary (pre-2026-05-14) hits this when they run `arcflow upgrade`. The fallback `curl | sh` install URL also points at a domain (`oz-web-omega.vercel.app`) that doesn't match what docs + cookbooks publish. Two of three recovery paths from a stale install are broken.

Real impact:
- Customers who installed before 2026-05-14 cannot upgrade through the documented `arcflow upgrade` flow.
- The error message they see is misleading — a filesystem error rather than a release-channel error — making self-diagnosis hard.
- The fallback URL they see in the CLI doesn't match the URL they see in the docs.

The bug isn't field-newly-observed (it's been latent since 2026-05-14), but every new customer that installed a v1.x binary and tries to upgrade hits it.

## What's being asked

Build-owner picks one of three release-channel dispositions and commits the corresponding fix:

### Disposition A — Migrate the v1.x channel to redirect at v0.x

Land a release-channel change so that a v1.x-installed binary's `arcflow upgrade` resolves "latest" to the current v0.8.x cut. Possible shapes:

- The release-matrix.json (or upgrade-manifest, whichever the CLI reads) gains an `upgrade_to: "0.8.x"` redirect for tags below 1.0.
- The `arcflow upgrade` code path detects "current is v1.x; latest line is v0.x" and bypasses the version-comparison guard.

Best for customers — they get the upgrade automatically. Worst for the CLI code path — needs a one-time line-bridge that has to be removed when v1.0 production-ready ships.

### Disposition B — Keep the channels split; document the manual reinstall path

The v1.x channel stays retired (no further tags). The CLI keeps reporting "no upgrade available" or "v1.x line retired." Customers reinstall via the canonical install URL.

In this case, DOC owns an upgrade page (`docs/upgrade.mdx`) documenting:
- "If you installed before 2026-05-14, run the canonical install command — `arcflow upgrade` from v1.x cannot resolve the current v0.8.x line."
- The canonical install URL (once confirmed; see install-URL question below).

Simplest disposition; worst customer experience for the in-the-field stale installs.

### Disposition C — Surface a typed error `INSTALL_LINE_RETIRED` (recommended)

Closes the typed-error gap that the SR-CONC-A1 and counterfactual primitives already established as canonical. The upgrade path detects the v1.x → v0.x line move and emits:

```json
{
  "class": "Installation",
  "code": "INSTALL_LINE_RETIRED",
  "message": "Your installed arcflow (v1.6.0) is on the retired v1.x line. The current line is v0.8.x. Reinstall via the canonical install command.",
  "recovery_suggestion": "curl -fsSL https://staging.oz.com/install/arcflow | sh"
}
```

Best of both worlds: customers see a typed, structured error pointing at the recovery, and the upgrade path doesn't carry a v1.x-bridge forever. The 404 misclassification also goes away — the upgrader hits this branch *before* attempting the download.

DOC's recommendation: Disposition C.

## Install-URL question (separate from upgrade-channel disposition)

The CLI fallback says `https://oz-web-omega.vercel.app/install_arcflow`. Cookbooks + docs + broadcasts say `https://staging.oz.com/install/arcflow`. Which is canonical?

- If `staging.oz.com/install/arcflow` is canonical: the CLI has a stale baked-in string; reissue a binary that points at the right URL.
- If `oz-web-omega.vercel.app/install_arcflow` is canonical: docs + cookbooks need to update.
- If both are valid (one is the underlying Vercel deployment; the other is the brand-clean URL fronting it): document the relationship so the customer-facing message uses the brand URL.

## What DOC can do this cycle

While AF picks a disposition, DOC can:

1. **Author `docs/upgrade.mdx`** stub describing the v1.x → v0.x line move at a high level. Pre-positions for Disposition B if AF picks that; harmless under Disposition A or C.
2. **Audit cookbooks + AGENTS.md + llms.txt for install-URL consistency** once AF confirms the canonical URL.
3. **Add an "If you installed before 2026-05-14"** callout to `docs/installation.mdx` pointing customers at the reinstall path.

DOC does not pre-author the upgrade page until AF picks the disposition — the page reads differently under A (no page needed; just release notes), B (full manual-reinstall walkthrough), and C (one-line "if you see `INSTALL_LINE_RETIRED`, here's why").

## Lifecycle

This message stays `open` until AF lands the disposition + fix commit. Then `resolved` + moves to `resolved/` per the standard federation lifecycle.

If urgency increases (customer-reported regressions multiply), DOC bumps severity from `high` to `blocker`.
