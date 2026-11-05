#!/usr/bin/env bash
# Install or upgrade Recordly.
# Usage: bash install_recordly.sh [--from-source]
#   (default)      macOS: Homebrew cask, upgraded when already installed
#   --from-source  clone webadderallorg/Recordly into ~/tools/recordly and build it

set -euo pipefail

REPO_URL="https://github.com/webadderallorg/Recordly.git"
INSTALL_DIR="$HOME/tools/recordly"
APP="/Applications/Recordly.app"
MODE="cask"

case "${1:-}" in
    "") ;;
    --from-source) MODE="source" ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 2 ;;
esac

OS="$(uname -s)"

app_version() {
    defaults read "$APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "unknown"
}

check_gatekeeper() {
    if spctl -a "$APP" 2>/dev/null; then
        echo "Gatekeeper: accepted."
    else
        echo "Gatekeeper rejected $APP." >&2
        echo "Inspect it first: spctl -a -vv \"$APP\"; codesign -dv --verbose=2 \"$APP\"" >&2
        echo "Clear quarantine only once the signature checks out: xattr -rd com.apple.quarantine \"$APP\"" >&2
        exit 1
    fi
}

if [ "$MODE" = "cask" ]; then
    if [ "$OS" != "Darwin" ]; then
        echo "The Homebrew cask is macOS only. On Linux use --from-source, the release AppImage, or 'yay -S recordly-bin'." >&2
        exit 2
    fi
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew not found. Install it from https://brew.sh, or rerun with --from-source." >&2
        exit 1
    fi

    if brew list --cask recordly >/dev/null 2>&1; then
        echo "Recordly $(app_version) installed through Homebrew. Checking for an upgrade..."
        brew upgrade --cask recordly
    elif [ -d "$APP" ]; then
        echo "$APP ($(app_version)) exists but Homebrew does not manage it."
        echo "Leaving it in place. To hand it to Homebrew: brew install --cask --force recordly"
    else
        brew install --cask recordly
    fi

    echo "Recordly $(app_version) at $APP"
    check_gatekeeper
    exit 0
fi

# --from-source
for cmd in git node npm; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: $cmd is required but not found." >&2
        case "$cmd" in
            git)  echo "Install: xcode-select --install (macOS) or apt install git (Linux)" >&2 ;;
            node) echo "Install: brew install node (macOS) or see https://nodejs.org/" >&2 ;;
            npm)  echo "npm ships with Node.js; reinstall Node if it is missing" >&2 ;;
        esac
        exit 1
    fi
done
if [ "$OS" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1; then
    echo "ERROR: Xcode Command Line Tools are required for the native capture helpers: xcode-select --install" >&2
    exit 1
fi

echo "Node.js $(node --version), npm $(npm --version)"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Existing clone at $INSTALL_DIR; pulling..."
    cd "$INSTALL_DIR"
    ORIGIN="$(git remote get-url origin 2>/dev/null || echo none)"
    if [ "$ORIGIN" != "$REPO_URL" ] && [ "$ORIGIN" != "${REPO_URL%.git}" ]; then
        echo "Note: origin is $ORIGIN, not $REPO_URL. Pulling from origin as configured."
    fi
    if ! git pull --ff-only; then
        echo "ERROR: cannot fast-forward $INSTALL_DIR. Resolve the local changes there, or remove the clone and rerun." >&2
        exit 1
    fi
else
    echo "Cloning $REPO_URL into $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "Installing dependencies..."
npm install

case "$OS" in
    Darwin)
        npm run build:mac
        BUILT=$(find dist -maxdepth 3 -name "Recordly.app" 2>/dev/null | head -1 || true)
        if [ -n "$BUILT" ]; then
            echo "Built app: $INSTALL_DIR/$BUILT"
            echo "A local build is unsigned. If macOS refuses to open it: xattr -rd com.apple.quarantine \"$INSTALL_DIR/$BUILT\""
        else
            echo "WARNING: no Recordly.app under dist/. Check: ls -la $INSTALL_DIR/dist/" >&2
        fi
        ;;
    Linux)
        npm run build:linux
        APPIMAGE=$(find dist -maxdepth 3 -name "*.AppImage" 2>/dev/null | head -1 || true)
        if [ -n "$APPIMAGE" ]; then
            chmod +x "$APPIMAGE"
            echo "Built app: $INSTALL_DIR/$APPIMAGE"
        else
            echo "WARNING: no .AppImage under dist/. Check: ls -la $INSTALL_DIR/dist/" >&2
        fi
        ;;
    *)
        echo "ERROR: unsupported platform $OS. Recordly builds on macOS and Linux here; Windows uses the release installer." >&2
        exit 1
        ;;
esac

echo "Launch with: bash $(dirname "$0")/launch_recordly.sh"
