#!/bin/sh
# ArcFlow installer — detects platform and downloads the correct binary.
# Usage: curl -fsSL https://oz.com/install | sh

set -e

REPO="ozinc/arcflow"
BASE_URL="https://github.com/${REPO}/releases"
INSTALL_DIR="${ARCFLOW_INSTALL_DIR:-$HOME/.arcflow/bin}"

# Detect platform
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
  linux)  PLATFORM="linux" ;;
  darwin) PLATFORM="darwin" ;;
  *)      echo "Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
  x86_64|amd64)   ARCH="x64" ;;
  aarch64|arm64)   ARCH="arm64" ;;
  *)               echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Detect libc (Linux only)
LIBC=""
if [ "$PLATFORM" = "linux" ]; then
  if ldd --version 2>&1 | grep -qi musl; then
    LIBC="-musl"
  else
    LIBC="-gnu"
  fi
fi

# Get latest version
VERSION="${ARCFLOW_VERSION:-}"

if [ -z "$VERSION" ]; then
  VERSION=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name"' | sed 's/.*"v\(.*\)".*/\1/')
fi

if [ -z "$VERSION" ]; then
  echo "Failed to detect latest version. Check https://github.com/${REPO}/releases"
  exit 1
fi

ASSET="arcflow-${VERSION}-${PLATFORM}-${ARCH}${LIBC}.tar.gz"
URL="${BASE_URL}/download/v${VERSION}/${ASSET}"

echo "Installing ArcFlow v${VERSION} (${PLATFORM}-${ARCH}${LIBC})..."
echo "  From: $URL"
echo "  To:   $INSTALL_DIR"

# Download and extract
mkdir -p "$INSTALL_DIR"
curl -fsSL "$URL" | tar xz -C "$INSTALL_DIR"

# Verify
if [ -x "$INSTALL_DIR/arcflow" ]; then
  echo ""
  echo "ArcFlow v${VERSION} installed to $INSTALL_DIR/arcflow"
  echo ""
  # Check if in PATH
  if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
      zsh)  RC="$HOME/.zshrc" ;;
      bash) RC="$HOME/.bashrc" ;;
      fish) RC="$HOME/.config/fish/config.fish" ;;
      *)    RC="$HOME/.profile" ;;
    esac
    echo "Add to your PATH:"
    echo "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> $RC"
    echo "  source $RC"
  fi
  echo ""
  echo "Get started:"
  echo "  arcflow --playground"
else
  echo "Installation failed. Binary not found at $INSTALL_DIR/arcflow"
  exit 1
fi
