#!/usr/bin/env bash
# Vendors conformance data from the engine repo into docs/reference/data/.
# Maintainer-only — outside contributors do not need to run this.
#
# Source priority:
#   1. ../arcflow (sibling checkout) — fast path for co-developed PRs
#   2. ARCFLOW_RELEASE_URL env var (release artifact tarball) — CI / fresh clones
#
# After running, regenerate MDX with: scripts/generate-reference.py

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/docs/reference/data"
ENGINE_LOCAL="${ARCFLOW_ENGINE_PATH:-$REPO_ROOT/../arcflow}"

mkdir -p "$DEST"

copy_from_local() {
  local engine="$1"
  echo "Sourcing from local checkout: $engine"

  cp "$engine/docs/conformance/gql-conformance.json"        "$DEST/gql-conformance.json"
  cp "$engine/docs/conformance/arcflow-extensions-catalog.md" "$DEST/arcflow-extensions-catalog.md"
  cp "$engine/conformance/state.json"                        "$DEST/conformance-state.json"
  cp "$engine/conformance/reports/extensions.md"             "$DEST/extension-regression.md"

  # Engine version + sync timestamp for downstream reproducibility
  local version
  version="$(jq -r '.version' "$DEST/gql-conformance.json")"
  cat > "$DEST/SYNC.json" <<EOF
{
  "engine_version": "$version",
  "synced_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "local:$engine",
  "source_commit": "$(git -C "$engine" rev-parse HEAD 2>/dev/null || echo 'unknown')"
}
EOF
}

copy_from_release() {
  local url="$1"
  echo "Sourcing from release artifact: $url"
  echo "ERROR: release-artifact path not yet implemented." >&2
  echo "Until the engine releases a conformance bundle, run with a sibling checkout at $ENGINE_LOCAL." >&2
  exit 2
}

if [[ -d "$ENGINE_LOCAL" && -f "$ENGINE_LOCAL/docs/conformance/gql-conformance.json" ]]; then
  copy_from_local "$ENGINE_LOCAL"
elif [[ -n "${ARCFLOW_RELEASE_URL:-}" ]]; then
  copy_from_release "$ARCFLOW_RELEASE_URL"
else
  echo "ERROR: no engine source found." >&2
  echo "  Set ARCFLOW_ENGINE_PATH to a sibling arcflow checkout, or" >&2
  echo "  set ARCFLOW_RELEASE_URL to a release-artifact tarball." >&2
  exit 1
fi

echo "Synced to $DEST"
echo "  $(ls -1 "$DEST" | wc -l | tr -d ' ') files"
echo "Next: scripts/generate-reference.py"
