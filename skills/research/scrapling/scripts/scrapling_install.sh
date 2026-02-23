#!/usr/bin/env bash
# scrapling_install.sh -- One-shot Scrapling installation and verification
#
# Installs scrapling[all] via uv, runs browser setup, and verifies.
set -euo pipefail

echo "==> Installing Scrapling with all extras..."
uv pip install --system "scrapling[all]"

echo ""
echo "==> Installing browser dependencies (Chromium + system deps)..."
scrapling install

echo ""
echo "==> Verifying installation..."
python3 -c "
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from scrapling.parser import Selector
print('  All fetchers available: Fetcher, DynamicFetcher, StealthyFetcher')
print('  Parser available: Selector')
"

echo ""
echo "==> Checking CLI..."
scrapling --version 2>/dev/null || echo "  CLI installed (no --version flag)"
which scrapling

echo ""
echo "Scrapling installation complete."
