#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: ane_stealth_fetch.sh <url> [site-type]"
  echo ""
  echo "Site types: scholar, pubmed, jstor, persee, perseus, academia,"
  echo "            cdli, oracc, sefaria, general"
  echo "If omitted, auto-detects from URL domain."
  exit 1
}

[ $# -lt 1 ] && usage

URL="$1"
SITE_TYPE="${2:-auto}"

case "$URL" in
  https://*|http://*) ;;
  *) echo "Error: only http:// and https:// URLs supported" >&2; exit 1 ;;
esac

if ! command -v obscura &>/dev/null && [ ! -x ~/tools/obscura/obscura ]; then
  echo "Error: obscura not found. Install to ~/tools/obscura/ or add to PATH." >&2
  echo "Fallback: use 'firecrawl scrape URL --only-main-content' instead." >&2
  exit 1
fi

OBSCURA="${OBSCURA:-$(command -v obscura 2>/dev/null || echo ~/tools/obscura/obscura)}"

if [ "$SITE_TYPE" = "auto" ]; then
  case "$URL" in
    *scholar.google.com*) SITE_TYPE="scholar" ;;
    *pubmed.ncbi.nlm.nih.gov*) SITE_TYPE="pubmed" ;;
    *jstor.org*) SITE_TYPE="jstor" ;;
    *persee.fr*) SITE_TYPE="persee" ;;
    *perseus.tufts.edu*) SITE_TYPE="perseus" ;;
    *academia.edu*) SITE_TYPE="academia" ;;
    *cdli.earth*|*cdli.ucla.edu*) SITE_TYPE="cdli" ;;
    *oracc.museum.upenn.edu*) SITE_TYPE="oracc" ;;
    *sefaria.org*) SITE_TYPE="sefaria" ;;
    *) SITE_TYPE="general" ;;
  esac
fi

case "$SITE_TYPE" in
  scholar)
    EVAL_JS="JSON.stringify(Array.from(document.querySelectorAll('.gs_r.gs_or')).slice(0,10).map(r=>({title:r.querySelector('.gs_rt')?.textContent||'',authors:r.querySelector('.gs_a')?.textContent||'',snippet:r.querySelector('.gs_rs')?.textContent?.substring(0,200)||'',cited_by:r.querySelector('.gs_fl a')?.textContent?.match(/Cited by (\d+)/)?.[1]||'0',pdf_url:r.querySelector('.gs_or_ggsm a')?.href||'',source_url:window.location.href})))"
    ;;
  pubmed)
    EVAL_JS="JSON.stringify({title:document.querySelector('.heading-title')?.textContent?.trim()||document.title,authors:Array.from(document.querySelectorAll('.authors-list .full-name')).map(e=>e.textContent),abstract:document.querySelector('.abstract-content')?.textContent?.trim()?.substring(0,2000)||'',doi:document.querySelector('.id-link[data-ga-action=DOI]')?.textContent?.trim()||'',year:document.querySelector('.cit')?.textContent?.match(/\d{4}/)?.[0]||'',source_url:window.location.href})"
    ;;
  jstor)
    EVAL_JS="JSON.stringify({title:document.title,abstract:document.querySelector('.abstract')?.textContent?.trim()||'',source_url:window.location.href})"
    ;;
  persee)
    EVAL_JS="JSON.stringify({title:document.title,meta:document.querySelector('meta[name=description]')?.content||'',hasArticle:!!document.querySelector('article'),source_url:window.location.href})"
    ;;
  perseus)
    EVAL_JS="JSON.stringify({title:document.title,text:document.querySelector('.text_container')?.textContent?.substring(0,2000)||'',source_url:window.location.href})"
    ;;
  academia)
    EVAL_JS="JSON.stringify({title:document.title,linkCount:document.querySelectorAll('a').length,source_url:window.location.href})"
    ;;
  cdli)
    EVAL_JS="JSON.stringify({title:document.title,designation:document.querySelector('.artifact-designation,.designation,h1')?.textContent?.trim()||'',period:document.querySelector('.period,[data-field=period]')?.textContent?.trim()||'',genre:document.querySelector('.genre,[data-field=genre]')?.textContent?.trim()||'',atf_preview:document.querySelector('.atf,pre,.transliteration')?.textContent?.substring(0,2000)||'',source_url:window.location.href})"
    ;;
  oracc)
    EVAL_JS="JSON.stringify({title:document.title,project:document.querySelector('.project-name,h1')?.textContent?.trim()||'',transliteration:document.querySelector('.transliteration,.t1,#Transliteration')?.textContent?.substring(0,2000)||'',translation:document.querySelector('.translation,.e,#Translation')?.textContent?.substring(0,2000)||'',source_url:window.location.href})"
    ;;
  sefaria)
    EVAL_JS="JSON.stringify({title:document.title,hebrew:document.querySelector('.he,.hebrewText')?.textContent?.substring(0,2000)||'',english:document.querySelector('.en,.englishText')?.textContent?.substring(0,2000)||'',ref:document.querySelector('.referenceName,h1')?.textContent?.trim()||'',source_url:window.location.href})"
    ;;
  general)
    EVAL_JS="JSON.stringify({title:document.title,text:document.body?.innerText?.substring(0,3000)||'',source_url:window.location.href})"
    ;;
  *)
    echo "Unknown site type: $SITE_TYPE" >&2
    exit 1
    ;;
esac

"$OBSCURA" fetch --stealth --quiet "$URL" --eval "$EVAL_JS"
