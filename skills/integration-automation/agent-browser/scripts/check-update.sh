#!/bin/bash
# check-update.sh — Check if agent-browser is up to date and optionally update
#
# Usage:
#   check-update.sh          # Check only
#   check-update.sh --update # Check and update if behind

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$SKILL_DIR/bin"
REPO="vercel-labs/agent-browser"

# Get local version
LOCAL_VERSION=$("$BIN_DIR/agent-browser" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")

# Get latest release from GitHub
LATEST_VERSION=$(gh release list --repo "$REPO" --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null | sed 's/^v//')

if [ -z "$LATEST_VERSION" ]; then
  echo "Failed to fetch latest version from GitHub. Is gh CLI authenticated?"
  exit 1
fi

echo "Local:  v${LOCAL_VERSION}"
echo "Latest: v${LATEST_VERSION}"

if [ "$LOCAL_VERSION" = "$LATEST_VERSION" ]; then
  echo "Up to date."
  exit 0
fi

echo "Update available!"

if [ "${1:-}" != "--update" ]; then
  echo "Run with --update to download v${LATEST_VERSION}"
  exit 0
fi

# Detect platform
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$OS" in darwin) OS="darwin" ;; linux) OS="linux" ;; esac
case "$ARCH" in x86_64|amd64) ARCH="x64" ;; aarch64|arm64) ARCH="arm64" ;; esac

BINARY_NAME="agent-browser-${OS}-${ARCH}"
TARGET="$BIN_DIR/$BINARY_NAME"

echo "Downloading $BINARY_NAME v${LATEST_VERSION}..."
gh release download "v${LATEST_VERSION}" \
  --repo "$REPO" \
  --pattern "$BINARY_NAME" \
  --output "$TARGET" \
  --clobber

chmod +x "$TARGET"

# Verify
NEW_VERSION=$("$BIN_DIR/agent-browser" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
echo "Updated to v${NEW_VERSION}"
