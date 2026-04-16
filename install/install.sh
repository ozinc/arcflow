#!/bin/sh
# ArcFlow installer
# Usage: curl -fsSL https://oz.com/install | sh
#
# This script is the canonical source. It is deployed to oz.com/install
# via oz-platform/apps/cloud/website/public/install.
#
# When modifying: update BOTH files and keep them identical.
#   arcflow-docs/install/install.sh  ← source of truth (this file)
#   oz-platform/.../public/install   ← deployed copy (oz.com/install)
#
# Naming convention:
#   arcflow-{VERSION}-{OS}-{ARCH}[-{LIBC}].tar.gz
#   OS:   darwin | linux
#   ARCH: arm64 | x86_64
#   LIBC: -gnu | -musl  (Linux only)
#
# Environment overrides:
#   ARCFLOW_VERSION      — install a specific version instead of latest
#   ARCFLOW_INSTALL_DIR  — install to a custom directory (default: ~/.arcflow/bin)

set -e

# ── Configuration ────────────────────────────────────────────────────────────

R2_BASE="https://pub-a0a196dbe10340f8af22524547fdd476.r2.dev/releases/arcflow"
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

resolve_version() {
  if [ -n "${ARCFLOW_VERSION:-}" ]; then
    VERSION="${ARCFLOW_VERSION#v}"
    return
  fi

  if command -v curl >/dev/null 2>&1; then
    VERSION="$(curl -fsSL "${R2_BASE}/latest.txt" 2>/dev/null || true)"
  elif command -v wget >/dev/null 2>&1; then
    VERSION="$(wget -qO- "${R2_BASE}/latest.txt" 2>/dev/null || true)"
  fi

  VERSION="$(printf '%s' "${VERSION}" | tr -d '[:space:]')"

  if [ -z "$VERSION" ]; then
    echo "Error: could not resolve latest version from ${R2_BASE}/latest.txt"
    echo "Set ARCFLOW_VERSION=x.y.z to install a specific version."
    exit 1
  fi
}

# ── Download and install ─────────────────────────────────────────────────────

download_and_install() {
  TARBALL="arcflow-${VERSION}-${PLATFORM}.tar.gz"
  URL="${R2_BASE}/${VERSION}/${TARBALL}"
  SHA256URL="${R2_BASE}/${VERSION}/SHA256SUMS"

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
      echo "Build from source: cargo install arcflow-cli"
      exit 1
    fi
  else
    if ! wget -q --show-progress "$URL" -O "${TMPDIR}/${TARBALL}"; then
      echo "Error: download failed. Check https://oz.com/install for troubleshooting."
      exit 1
    fi
  fi

  # Verify SHA256
  if command -v sha256sum >/dev/null 2>&1; then
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$SHA256URL" -o "${TMPDIR}/SHA256SUMS" 2>/dev/null || true
    fi
    if [ -f "${TMPDIR}/SHA256SUMS" ]; then
      EXPECTED="$(grep " ${TARBALL}$" "${TMPDIR}/SHA256SUMS" | awk '{print $1}')"
      if [ -n "$EXPECTED" ]; then
        ACTUAL="$(sha256sum "${TMPDIR}/${TARBALL}" | awk '{print $1}')"
        if [ "$EXPECTED" != "$ACTUAL" ]; then
          echo "Error: SHA256 mismatch for ${TARBALL}"
          echo "  Expected: $EXPECTED"
          echo "  Actual:   $ACTUAL"
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
}

main
