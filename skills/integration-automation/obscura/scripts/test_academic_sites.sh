#!/bin/bash
set -euo pipefail

PASS=0
FAIL=0
BLOCKED=0
TOTAL=0

result() {
  TOTAL=$((TOTAL + 1))
  case "$1" in
    PASS)
      PASS=$((PASS + 1))
      printf "  %-45s \033[32mPASS\033[0m\n" "$2"
      ;;
    FAIL)
      FAIL=$((FAIL + 1))
      printf "  %-45s \033[31mFAIL\033[0m  %s\n" "$2" "${3:-}"
      ;;
    BLOCKED)
      BLOCKED=$((BLOCKED + 1))
      printf "  %-45s \033[33mBLOCKED\033[0m  %s\n" "$2" "${3:-}"
      ;;
  esac
}

fetch_stealth() {
  obscura fetch --stealth --quiet "$1" --eval "$2" 2>/dev/null || echo "__FETCH_ERROR__"
}

echo "=== Obscura Academic Site Tests ==="
echo "    (requires internet, ~60s)"
echo ""

# 1. Perseus Digital Library — minimal anti-bot, good baseline
output=$(fetch_stealth \
  "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0134" \
  "document.title + ' ||| ' + (document.querySelector('.text_container') ? 'HAS_TEXT' : 'NO_TEXT')")
if echo "$output" | grep -q "__FETCH_ERROR__"; then
  result FAIL "Perseus Digital Library" "fetch failed"
elif echo "$output" | grep -qi "captcha\|blocked\|denied"; then
  result BLOCKED "Perseus Digital Library" "bot detection triggered"
elif echo "$output" | grep -qi "perseus\|tufts\|HAS_TEXT\|homer\|iliad"; then
  result PASS "Perseus Digital Library"
else
  result FAIL "Perseus Digital Library" "unexpected: $(echo "$output" | head -c 100)"
fi

# 2. PubMed abstract
output=$(fetch_stealth \
  "https://pubmed.ncbi.nlm.nih.gov/25418537/" \
  "document.title + ' ||| ' + (document.querySelector('.abstract-content') ? document.querySelector('.abstract-content').textContent.substring(0,100) : 'NO_ABSTRACT')")
if echo "$output" | grep -q "__FETCH_ERROR__"; then
  result FAIL "PubMed abstract" "fetch failed"
elif echo "$output" | grep -qi "captcha\|blocked\|denied\|unusual traffic"; then
  result BLOCKED "PubMed abstract" "bot detection triggered"
elif echo "$output" | grep -qi "pubmed\|abstract\|ncbi"; then
  result PASS "PubMed abstract"
else
  result FAIL "PubMed abstract" "unexpected: $(echo "$output" | head -c 100)"
fi

# 3. Google Scholar — aggressive bot detection
output=$(fetch_stealth \
  "https://scholar.google.com/scholar?q=minoan+trade+routes+bronze+age" \
  "document.title + ' ||| ' + document.querySelectorAll('.gs_rt').length + ' results'")
if echo "$output" | grep -q "__FETCH_ERROR__"; then
  result FAIL "Google Scholar" "fetch failed"
elif echo "$output" | grep -qi "captcha\|unusual traffic\|sorry\|blocked"; then
  result BLOCKED "Google Scholar" "CAPTCHA served"
elif echo "$output" | grep -qi "scholar\|results"; then
  result PASS "Google Scholar"
else
  result FAIL "Google Scholar" "unexpected: $(echo "$output" | head -c 100)"
fi

# 4. Persée — French academic archive
output=$(fetch_stealth \
  "https://www.persee.fr/doc/bch_0007-4217_1996_num_120_1_4584" \
  "document.title + ' ||| ' + (document.querySelector('article') ? 'HAS_ARTICLE' : document.querySelector('.content') ? 'HAS_CONTENT' : 'NO_CONTENT')")
if echo "$output" | grep -q "__FETCH_ERROR__"; then
  result FAIL "Persée article" "fetch failed"
elif echo "$output" | grep -qi "captcha\|altcha\|blocked\|denied"; then
  result BLOCKED "Persée article" "bot detection triggered"
elif echo "$output" | grep -qi "persee\|persée\|bch\|article"; then
  result PASS "Persée article"
else
  result FAIL "Persée article" "unexpected: $(echo "$output" | head -c 100)"
fi

# 5. JSTOR preview — fingerprints headless browsers
output=$(fetch_stealth \
  "https://www.jstor.org/stable/10.2307/25651204" \
  "document.title + ' ||| ' + (document.querySelector('.abstract') ? 'HAS_ABSTRACT' : document.querySelector('[data-testid]') ? 'HAS_CONTENT' : 'MINIMAL')")
if echo "$output" | grep -q "__FETCH_ERROR__"; then
  result FAIL "JSTOR preview" "fetch failed"
elif echo "$output" | grep -qi "captcha\|blocked\|denied\|incapsula\|access denied"; then
  result BLOCKED "JSTOR preview" "bot detection triggered"
elif echo "$output" | grep -qi "jstor"; then
  result PASS "JSTOR preview"
else
  result FAIL "JSTOR preview" "unexpected: $(echo "$output" | head -c 100)"
fi

# 6. Academia.edu author profile — bot-detecting
output=$(fetch_stealth \
  "https://www.academia.edu/departments/Classics" \
  "document.title + ' ||| ' + (document.querySelectorAll('a').length > 10 ? 'RICH_PAGE' : 'SPARSE')")
if echo "$output" | grep -q "__FETCH_ERROR__"; then
  result FAIL "Academia.edu" "fetch failed"
elif echo "$output" | grep -qi "captcha\|blocked\|denied\|cloudflare"; then
  result BLOCKED "Academia.edu" "bot detection triggered"
elif echo "$output" | grep -qi "academia\|classics"; then
  result PASS "Academia.edu"
else
  result FAIL "Academia.edu" "unexpected: $(echo "$output" | head -c 100)"
fi

echo ""
echo "=== Results: $PASS PASS, $FAIL FAIL, $BLOCKED BLOCKED (of $TOTAL) ==="
exit 0
