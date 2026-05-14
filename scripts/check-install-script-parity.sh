#!/usr/bin/env bash
# Verify install/install.sh (SoT in this repo) matches the deployed copy
# served from staging.oz.com/install/arcflow.
#
# Run locally before merging install.sh changes:
#   ./scripts/check-install-script-parity.sh
#
# CI invocation: .github/workflows/install-script-parity.yml
#
# Exit codes:
#   0  — byte-identical
#   1  — drift detected (SoT differs from deployed)
#   2  — fetch failed (network / staging.oz.com down)
#
# This is the byte-identical fitness check called out in
# MRL-DOC-2026-05-14-001 (install-script CI). The deployed mirror at
# oz-platform/apps/cloud/website/public/install/arcflow must stay in
# lockstep with this repo's install/install.sh.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOT="$REPO_ROOT/install/install.sh"
DEPLOYED_URL="${INSTALL_PARITY_URL:-https://staging.oz.com/install/arcflow}"

if [[ ! -f "$SOT" ]]; then
  echo "FATAL: source-of-truth not found at $SOT" >&2
  exit 2
fi

tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT

if ! curl -fsSL --max-time 30 "$DEPLOYED_URL" -o "$tmpfile"; then
  echo "FATAL: failed to fetch deployed copy from $DEPLOYED_URL" >&2
  echo "  (network outage, oz.com down, or URL changed — not a parity failure)" >&2
  exit 2
fi

sot_sha=$(shasum -a 256 "$SOT"     | awk '{print $1}')
dep_sha=$(shasum -a 256 "$tmpfile" | awk '{print $1}')

if [[ "$sot_sha" == "$dep_sha" ]]; then
  echo "OK — install/install.sh matches $DEPLOYED_URL"
  echo "  sha256: $sot_sha"
  exit 0
fi

echo "FAIL — install/install.sh has drifted from $DEPLOYED_URL" >&2
echo "  source-of-truth sha256: $sot_sha" >&2
echo "  deployed copy sha256:   $dep_sha" >&2
echo >&2
echo "Likely cause: install/install.sh was edited here but the deployed mirror" >&2
echo "(oz-platform/apps/cloud/website/public/install/arcflow) was not synced," >&2
echo "or vice versa." >&2
echo >&2
echo "Diff (SoT vs deployed):" >&2
diff -u "$SOT" "$tmpfile" >&2 || true
exit 1
