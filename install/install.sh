#!/bin/sh
# ArcFlow installer — detects platform and downloads the correct binary.
# Usage: curl -fsSL https://arcflow.dev/install | sh

set -e

BASE_URL="${ARCFLOW_BASE_URL:-https://arcflow.dev/releases}"
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

# Get latest version (or use specified)
VERSION="${ARCFLOW_VERSION:-latest}"

if [ "$VERSION" = "latest" ]; then
  VERSION=$(curl -fsSL "${BASE_URL}/latest/VERSION" 2>/dev/null || echo "")
fi

if [ -z "$VERSION" ]; then
  # Fallback: download latest directly
  ASSET="arcflow-latest-${PLATFORM}-${ARCH}${LIBC}.tar.gz"
  URL="${BASE_URL}/latest/${ASSET}"
else
  ASSET="arcflow-${VERSION}-${PLATFORM}-${ARCH}${LIBC}.tar.gz"
  URL="${BASE_URL}/v${VERSION}/${ASSET}"
fi

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
