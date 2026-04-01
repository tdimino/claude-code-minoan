#!/usr/bin/env bash
# Install Recordly — clone, build, and configure
# Usage: bash install_recordly.sh

set -euo pipefail

INSTALL_DIR="$HOME/tools/recordly"
REPO_URL="https://github.com/webadderall/Recordly.git"

echo "=== Recordly Installer ==="

# Check prerequisites
for cmd in git node npm; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd is required but not found."
        case "$cmd" in
            git)  echo "Install: xcode-select --install (macOS) or apt install git (Linux)" ;;
            node) echo "Install: brew install node (macOS) or see https://nodejs.org/" ;;
            npm)  echo "Install: npm ships with Node.js — reinstall Node if missing" ;;
        esac
        exit 1
    fi
done

echo "Node.js: $(node --version), npm: $(npm --version)"

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Existing install found at $INSTALL_DIR — pulling latest..."
    cd "$INSTALL_DIR"
    if ! git pull --ff-only 2>&1; then
        echo ""
        echo "ERROR: Could not fast-forward update. Your local install may have diverged."
        echo "Options:"
        echo "  1. cd $INSTALL_DIR && git stash && git pull --ff-only && git stash pop"
        echo "  2. Remove $INSTALL_DIR and re-run this installer for a clean install."
        exit 1
    fi
else
    echo "Cloning Recordly to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install dependencies
echo "Installing dependencies..."
if ! npm install 2>&1; then
    echo ""
    echo "ERROR: npm install failed."
    echo "Common causes:"
    echo "  - Node.js version mismatch (you have $(node --version))"
    echo "  - Missing build tools: xcode-select --install (macOS) or apt install build-essential (Linux)"
    echo "  - Network issues: check your connection and try again"
    exit 1
fi

# Detect platform and build
OS="$(uname -s)"
case "$OS" in
    Darwin)
        echo "Building for macOS..."
        if ! npm run build:mac 2>&1; then
            echo ""
            echo "ERROR: macOS build failed. Check output above for details."
            exit 1
        fi

        APP_PATH=$(find dist -name "Recordly.app" -maxdepth 3 2>/dev/null | head -1)
        if [ -n "$APP_PATH" ]; then
            xattr -rd com.apple.quarantine "$APP_PATH" || echo "Note: Could not remove quarantine flag. If macOS blocks the app, run: xattr -rd com.apple.quarantine $INSTALL_DIR/$APP_PATH"
            echo "Built app: $INSTALL_DIR/$APP_PATH"
        else
            echo "WARNING: Could not locate Recordly.app in dist/."
            echo "The build may have produced a .dmg or used a different name."
            echo "Check: ls -la $INSTALL_DIR/dist/"
        fi

        if [ -d "/Applications/Recordly.app" ]; then
            xattr -rd com.apple.quarantine "/Applications/Recordly.app" || echo "Note: Could not clear quarantine on /Applications/Recordly.app"
        fi
        ;;
    Linux)
        echo "Building for Linux..."
        if ! npm run build:linux 2>&1; then
            echo ""
            echo "ERROR: Linux build failed. Check output above for details."
            exit 1
        fi

        APPIMAGE=$(find dist -name "*.AppImage" -maxdepth 3 2>/dev/null | head -1)
        if [ -n "$APPIMAGE" ]; then
            chmod +x "$APPIMAGE"
            echo "Built app: $INSTALL_DIR/$APPIMAGE"
        else
            echo "WARNING: Could not locate .AppImage in dist/."
            echo "Check: ls -la $INSTALL_DIR/dist/"
        fi
        ;;
    *)
        echo "ERROR: Unsupported platform: $OS. Recordly supports macOS and Linux."
        exit 1
        ;;
esac

echo ""
echo "=== Install complete ==="
echo "Install directory: $INSTALL_DIR"
echo "To launch: bash $(dirname "$0")/launch_recordly.sh"
