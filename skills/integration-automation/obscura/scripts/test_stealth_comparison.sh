#!/bin/bash
set -euo pipefail

echo "=== Obscura Stealth Comparison ==="
echo "    Obscura --stealth vs Obscura (no stealth) vs curl"
echo ""

printf "%-35s %-20s %-20s %-20s\n" "Detection Vector" "Obscura+Stealth" "Obscura(plain)" "curl"
printf "%-35s %-20s %-20s %-20s\n" "---" "---" "---" "---"

# navigator.webdriver
stealth_wd=$(obscura fetch --stealth --quiet https://example.com \
  --eval "String(navigator.webdriver)" 2>/dev/null || echo "ERROR")
plain_wd=$(obscura fetch --quiet https://example.com \
  --eval "String(navigator.webdriver)" 2>/dev/null || echo "ERROR")
printf "%-35s %-20s %-20s %-20s\n" "navigator.webdriver" "$stealth_wd" "$plain_wd" "n/a (no JS)"

# navigator.plugins.length
stealth_pl=$(obscura fetch --stealth --quiet https://example.com \
  --eval "String(navigator.plugins.length)" 2>/dev/null || echo "ERROR")
plain_pl=$(obscura fetch --quiet https://example.com \
  --eval "String(navigator.plugins.length)" 2>/dev/null || echo "ERROR")
printf "%-35s %-20s %-20s %-20s\n" "navigator.plugins.length" "$stealth_pl" "$plain_pl" "n/a"

# navigator.languages
stealth_lang=$(obscura fetch --stealth --quiet https://example.com \
  --eval "JSON.stringify(navigator.languages)" 2>/dev/null || echo "ERROR")
plain_lang=$(obscura fetch --quiet https://example.com \
  --eval "JSON.stringify(navigator.languages)" 2>/dev/null || echo "ERROR")
printf "%-35s %-20s %-20s %-20s\n" "navigator.languages" \
  "$(echo "$stealth_lang" | head -c 18)" \
  "$(echo "$plain_lang" | head -c 18)" "n/a"

# navigator.platform
stealth_pf=$(obscura fetch --stealth --quiet https://example.com \
  --eval "navigator.platform" 2>/dev/null || echo "ERROR")
plain_pf=$(obscura fetch --quiet https://example.com \
  --eval "navigator.platform" 2>/dev/null || echo "ERROR")
printf "%-35s %-20s %-20s %-20s\n" "navigator.platform" "$stealth_pf" "$plain_pf" "n/a"

# chrome.runtime presence
stealth_cr=$(obscura fetch --stealth --quiet https://example.com \
  --eval "typeof window.chrome !== 'undefined' && typeof window.chrome.runtime !== 'undefined' ? 'present' : 'absent'" 2>/dev/null || echo "ERROR")
plain_cr=$(obscura fetch --quiet https://example.com \
  --eval "typeof window.chrome !== 'undefined' && typeof window.chrome.runtime !== 'undefined' ? 'present' : 'absent'" 2>/dev/null || echo "ERROR")
printf "%-35s %-20s %-20s %-20s\n" "chrome.runtime" "$stealth_cr" "$plain_cr" "n/a"

# User-Agent string
stealth_ua=$(obscura fetch --stealth --quiet https://example.com \
  --eval "navigator.userAgent.substring(0,40)" 2>/dev/null || echo "ERROR")
plain_ua=$(obscura fetch --quiet https://example.com \
  --eval "navigator.userAgent.substring(0,40)" 2>/dev/null || echo "ERROR")
curl_ua=$(curl -sI https://example.com 2>/dev/null | head -1 | cut -c1-20 || echo "n/a")
printf "%-35s %-20s %-20s %-20s\n" "User-Agent (first 40 chars)" \
  "$(echo "$stealth_ua" | head -c 18)" \
  "$(echo "$plain_ua" | head -c 18)" \
  "$curl_ua"

echo ""
echo "=== Summary ==="
echo "  navigator.webdriver: Stealth=$stealth_wd, Plain=$plain_wd"
echo "    (undefined = stealthy, true = detectable)"
echo ""
echo "  Key: 'undefined' for webdriver and >0 for plugins.length"
echo "  indicate proper stealth camouflage."
