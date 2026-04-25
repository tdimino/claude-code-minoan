#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: academic_stealth_fetch.sh <url> [site-type]"
  echo ""
  echo "Site types: scholar, pubmed, jstor, persee, perseus, academia, general"
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

if [ "$SITE_TYPE" = "auto" ]; then
  case "$URL" in
    *scholar.google.com*) SITE_TYPE="scholar" ;;
    *pubmed.ncbi.nlm.nih.gov*) SITE_TYPE="pubmed" ;;
    *jstor.org*) SITE_TYPE="jstor" ;;
    *persee.fr*) SITE_TYPE="persee" ;;
    *perseus.tufts.edu*) SITE_TYPE="perseus" ;;
    *academia.edu*) SITE_TYPE="academia" ;;
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
  general)
    EVAL_JS="JSON.stringify({title:document.title,text:document.body?.innerText?.substring(0,3000)||'',source_url:window.location.href})"
    ;;
  *)
    echo "Unknown site type: $SITE_TYPE" >&2
    exit 1
    ;;
esac

obscura fetch --stealth --quiet "$URL" --eval "$EVAL_JS"
