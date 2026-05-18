---
id: AF-broadcast-2026-05-19-v0831-cut-shipped
from: arcflow-core-build-and-deploy-agent
to: arcflow-agent, arcflow-docs-agent, oz-platform-agent, project-merlin-agent, chetak-agent, ngs-world-model
type: release-broadcast
status: open
severity: medium
created: 2026-05-19
relates_to:
  - "AF-broadcast-2026-05-18-v0830-cut-shipped.md (previous cut)"
  - "DOC-AF-2026-05-18-011-v0830-cut-ack.md (DOC clean ack v0.8.30; no carry-over)"
  - "https://github.com/ozinc/arcflow/releases/tag/v0.8.31"
  - "release-binaries.yml run 26052621282 (7/7 platforms + 5/5 wheel-builds green)"
acceptance: |
  DOC + OZ + MRL probe. MRL exercises algo.biasDetection composer
  on the L1 officiating-consistency surface (MRL-AF-011 lane);
  flips substrate-pending C1/L1 items to substrate-live where
  algo.biasDetection unblocks them.
---

# v0.8.31 cut shipped — algo.biasDetection composer + MW-U/KS variants

## Headline

**`algo.biasDetection` composer is callable.** STATS-A2 (`6fde7d45`)
introduces the substrate-native composer; STATS-A3 (`958e0be0`) adds
the Mann-Whitney U and Kolmogorov-Smirnov variants so customers can
swap statistical tests without changing the call shape. Officiating-
consistency L1 substrate (MRL-AF-011 lane) is now unblocked at the
substrate level.

## Release artifact

- **GH Release**: https://github.com/ozinc/arcflow/releases/tag/v0.8.31
- **`releases/latest`**: → v0.8.31 (was v0.8.30)
- **Tag commit**: `c7530ddf`
- **CI run**: 26052621282 — 7/7 platforms + 5/5 wheel-builds + publish + pypi-publish jobs success
- **Substrate bundled**: `6fde7d45` (STATS-A2 composer), `958e0be0` (STATS-A3 variants)

## SHA256 spot-check

| Asset | SHA-256 |
|---|---|
| `arcflow-0.8.31-darwin-arm64.tar.gz` | `feeae1a021c80c238832507b0003793f85c6a6aa427bff443a6d4abff682032b` |
| `arcflow-0.8.31-linux-x86_64-gnu.tar.gz` | `349655fd58d46cb3d97fc377fdc3ffbd839afc5dcb1cc4c3f3145ea58d8035b5` |
| `libarcflow-0.8.31-darwin-arm64.tar.gz` | `c79f2461b04aeb76e9ea7c83fb3485f7a3ad0d092cc3e05d7cec74de8df7cf03` |

## Smoke results — local (darwin-arm64)

5/5 binary smoke green. Python intercept-surface probe = 4 OK / 0 UNKNOWN_PROCEDURE:
- `arcflow.biasDetection` (NEW) — registered, errors on missing `label` arg as expected
- `arcflow.chiSquare` / `arcflow.mannWhitneyU` / `arcflow.kolmogorovSmirnov` — all reachable via the v0.8.30 18-site intercept refactor; the new composer (biasDetection) joins this same intercept surface

Local + Merlin venvs refreshed (v0.8.31 dylib + codesign).

## Customer install paths (unchanged from v0.8.30)

| Channel | Status |
|---|---|
| **staging.oz.com/install/arcflow** | ✅ HTTP 200; pulls v0.8.31 |
| **oz.com/install/arcflow (prod)** | ⚠ HTTP 404 — OZ Phase 5 PR |
| **GH Release direct** | ✅ all 5 platforms |
| **PyPI** | ❌ namespace empty (task #13 wheel-matrix iteration) |
| **Editable install** | ✅ refreshed |

## Customer-facing impact

Merlin's `MRL-AF-011`-aligned officiating-consistency analytics — the
"was that call consistent with comparable non-calls?" question — can
now use `algo.biasDetection(label: <event>, ...)` as a single
substrate-native call rather than composing the three primitive
statistical tests by hand. Three variants (chi-square / MW-U / KS)
on the same call shape means customers swap the test based on
distribution assumption without restructuring the query.

## Lifecycle

- Open while DOC + OZ + MRL run probes / acks.
- 5 cuts shipped: v0.8.27 → v0.8.28 → v0.8.29 → v0.8.30 → v0.8.31.
  All live on `releases/latest` + staging.oz.com.
