#!/bin/sh
# ArcFlow installer
# Usage: curl -fsSL https://oz.com/install/arcflow | sh
#
# This script is the canonical source. It is deployed to oz.com/install/arcflow
# via oz-platform/apps/cloud/website/public/install/arcflow.
#
# When modifying: update BOTH files and keep them identical.
#   arcflow-docs/install/install.sh        ← source of truth (this file)
#   oz-platform/.../public/install/arcflow ← deployed copy (oz.com/install/arcflow)
#
# Release source: GitHub Releases on the public ozinc/arcflow repo.
# Binaries, SHA256SUMS, and release-matrix.json are all attached as
# release assets — see release-binaries.yml in arcflow-core.
#
# Naming convention:
#   arcflow-{VERSION}-{OS}-{ARCH}[-{LIBC}].tar.gz
#   OS:   darwin | linux
#   ARCH: arm64 | x86_64
#   LIBC: -gnu | -musl  (Linux only)
#
# Environment overrides:
#   ARCFLOW_VERSION      — install a specific version instead of latest
#                          (e.g. ARCFLOW_VERSION=0.7.2)
#   ARCFLOW_INSTALL_DIR  — install to a custom directory
#                          (default: ~/.arcflow/bin)
#   ARCFLOW_REPO         — override the release-host repo
#                          (default: ozinc/arcflow). Useful for mirrors
#                          or forks.

set -e

# ── Configuration ────────────────────────────────────────────────────────────

REPO="${ARCFLOW_REPO:-ozinc/arcflow}"
GH_RELEASES="https://github.com/${REPO}/releases"
INSTALL_DIR="${ARCFLOW_INSTALL_DIR:-$HOME/.arcflow/bin}"

# ── Platform detection ───────────────────────────────────────────────────────

detect_platform() {
  OS="$(uname -s)"
  ARCH="$(uname -m)"

  case "$OS" in
    Darwin) OS="darwin" ;;
    Linux)  OS="linux"  ;;
    *)
      echo "Unsupported OS: $OS"
      echo "Build from source: cargo install arcflow-cli"
      exit 1
      ;;
  esac

  case "$ARCH" in
    x86_64|amd64)  ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64"  ;;
    *)
      echo "Unsupported architecture: $ARCH"
      exit 1
      ;;
  esac

  # Linux only: detect libc variant
  LIBC=""
  if [ "$OS" = "linux" ]; then
    if ldd --version 2>&1 | grep -qi musl; then
      LIBC="-musl"
    else
      LIBC="-gnu"
    fi
  fi

  PLATFORM="${OS}-${ARCH}${LIBC}"
}

# ── Version resolution ───────────────────────────────────────────────────────

# Resolve the version to install. If ARCFLOW_VERSION is set, use that.
# Otherwise, follow GitHub Releases' /latest redirect to discover the
# current latest tag. The redirect target is
#   https://github.com/ozinc/arcflow/releases/tag/v<version>
# from which we extract <version>.
#
# Curl is the primary fetcher; wget falls back. Both can follow redirects
# and emit the final URL via -L plus the relevant write-out / output
# flags.
resolve_version() {
  if [ -n "${ARCFLOW_VERSION:-}" ]; then
    VERSION="${ARCFLOW_VERSION#v}"
    return
  fi

  REDIRECT_URL=""
  if command -v curl >/dev/null 2>&1; then
    REDIRECT_URL="$(curl -fsSL -o /dev/null -w '%{url_effective}' \
      "${GH_RELEASES}/latest" 2>/dev/null || true)"
  elif command -v wget >/dev/null 2>&1; then
    REDIRECT_URL="$(wget -q -S --max-redirect=10 -O /dev/null \
      "${GH_RELEASES}/latest" 2>&1 \
      | awk '/^[[:space:]]+Location:/ { url=$2 } END { print url }' || true)"
  fi

  # The canonical "a release exists" redirect target is
  # .../releases/tag/v<version>. Anything else — the bare .../releases
  # listing when zero releases exist, an unfollowed .../releases/latest,
  # a network-error empty string — means there is nothing to install.
  # Require the /tag/ segment before extracting the version (pattern-
  # positive guard; safer than excluding known-bad tail words like
  # "latest" or "releases" one at a time).
  VERSION=""
  case "$REDIRECT_URL" in
    */releases/tag/*)
      TAG="${REDIRECT_URL##*/}"
      VERSION="${TAG#v}"
      VERSION="$(printf '%s' "${VERSION}" | tr -d '[:space:]')"
      ;;
  esac

  if [ -z "$VERSION" ]; then
    echo "Error: no released version found at ${GH_RELEASES}/latest"
    echo "Set ARCFLOW_VERSION=x.y.z to install a specific version."
    echo ""
    echo "Browse available releases:"
    echo "  ${GH_RELEASES}"
    exit 1
  fi
}

# ── Download and install ─────────────────────────────────────────────────────

download_and_install() {
  TARBALL="arcflow-${VERSION}-${PLATFORM}.tar.gz"
  TAG="v${VERSION}"
  # /releases/download/<tag>/<asset> is the canonical download URL.
  # GitHub serves it via redirect-to-CDN; curl/wget follow -L.
  URL="${GH_RELEASES}/download/${TAG}/${TARBALL}"
  SHA256URL="${GH_RELEASES}/download/${TAG}/SHA256SUMS"

  TMPDIR="$(mktemp -d)"
  # shellcheck disable=SC2064
  trap 'rm -rf "$TMPDIR"' EXIT

  printf '\nInstalling ArcFlow v%s (%s)\n' "$VERSION" "$PLATFORM"
  printf '  From: %s\n' "$URL"
  printf '  To:   %s\n\n' "$INSTALL_DIR"

  if command -v curl >/dev/null 2>&1; then
    if ! curl -fsSL --progress-bar "$URL" -o "${TMPDIR}/${TARBALL}"; then
      echo ""
      echo "Error: binary not available for ${PLATFORM} in v${VERSION}."
      echo ""
      echo "Available platforms:"
      echo "  darwin-arm64, darwin-x86_64"
      echo "  linux-x86_64-gnu, linux-arm64-gnu"
      echo "  linux-x86_64-musl, linux-arm64-musl"
      echo ""
      echo "Browse: ${GH_RELEASES}/tag/${TAG}"
      echo "Build from source: cargo install arcflow-cli"
      exit 1
    fi
  else
    if ! wget -q --show-progress "$URL" -O "${TMPDIR}/${TARBALL}"; then
      echo "Error: download failed. Check ${GH_RELEASES} for available platforms."
      exit 1
    fi
  fi

  # Verify SHA256 against the SHA256SUMS aggregate file shipped on the
  # same release. GitHub Releases serves both atomically; a mismatch
  # means either the tarball or the SUMS file was tampered with on a
  # mirror, or you hit a partial download.
  if command -v sha256sum >/dev/null 2>&1; then
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$SHA256URL" -o "${TMPDIR}/SHA256SUMS" 2>/dev/null || true
    fi
    if [ -f "${TMPDIR}/SHA256SUMS" ]; then
      EXPECTED="$(grep "  ${TARBALL}$" "${TMPDIR}/SHA256SUMS" | awk '{print $1}')"
      if [ -n "$EXPECTED" ]; then
        ACTUAL="$(sha256sum "${TMPDIR}/${TARBALL}" | awk '{print $1}')"
        if [ "$EXPECTED" != "$ACTUAL" ]; then
          echo "Error: SHA256 mismatch for ${TARBALL}"
          echo "  Expected: $EXPECTED"
          echo "  Actual:   $ACTUAL"
          echo ""
          echo "For full cryptographic verification, install gh CLI and run:"
          echo "  gh attestation verify ${TARBALL} --owner ozinc"
          exit 1
        fi
      fi
    fi
  fi

  tar -xzf "${TMPDIR}/${TARBALL}" -C "$TMPDIR"

  mkdir -p "$INSTALL_DIR"
  INSTALLED=""
  for bin in arcflow arcflow-mcp arcflow-bridge; do
    BIN_PATH="$(find "$TMPDIR" -maxdepth 2 -name "$bin" -type f 2>/dev/null | head -1)"
    if [ -n "$BIN_PATH" ]; then
      mv "$BIN_PATH" "${INSTALL_DIR}/${bin}"
      chmod +x "${INSTALL_DIR}/${bin}"
      INSTALLED="${INSTALLED} ${bin}"
    fi
  done

  if [ -z "$INSTALLED" ]; then
    echo "Error: no arcflow binaries found in archive."
    exit 1
  fi
}

# ── PATH setup ───────────────────────────────────────────────────────────────

update_path() {
  if echo ":${PATH}:" | grep -q ":${INSTALL_DIR}:"; then
    return
  fi

  SHELL_NAME="$(basename "${SHELL:-/bin/sh}")"
  PROFILE=""
  case "$SHELL_NAME" in
    zsh)  PROFILE="$HOME/.zshrc" ;;
    bash)
      if [ -f "$HOME/.bash_profile" ]; then
        PROFILE="$HOME/.bash_profile"
      else
        PROFILE="$HOME/.bashrc"
      fi
      ;;
    fish) PROFILE="$HOME/.config/fish/config.fish" ;;
    *)    PROFILE="$HOME/.profile" ;;
  esac

  if [ -n "$PROFILE" ] && [ -f "$PROFILE" ]; then
    if ! grep -q "$INSTALL_DIR" "$PROFILE" 2>/dev/null; then
      if [ "$SHELL_NAME" = "fish" ]; then
        printf '\nfish_add_path "%s"\n' "$INSTALL_DIR" >> "$PROFILE"
      else
        printf '\nexport PATH="%s:$PATH"\n' "$INSTALL_DIR" >> "$PROFILE"
      fi
    fi
  fi
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
  detect_platform
  resolve_version
  download_and_install
  update_path

  printf '\nArcFlow v%s installed.\n' "$VERSION"
  printf 'Binaries:%s\n\n' "$INSTALLED"
  printf 'Run it now:\n'
  printf '  export PATH="%s:$PATH" && arcflow --help\n\n' "$INSTALL_DIR"
  printf 'Verify the install (optional, requires gh CLI):\n'
  printf '  gh attestation verify ~/.arcflow/bin/arcflow --owner ozinc\n\n'
  printf 'Release page: %s/tag/v%s\n' "$GH_RELEASES" "$VERSION"
}

main
