#!/usr/bin/env bash
# deepwiki - Fetch AI-generated documentation for any GitHub repo via DeepWiki
#
# Usage:
#   deepwiki owner/repo              # Fetch overview (table of contents + summary)
#   deepwiki owner/repo --toc        # Fetch just the table of contents (page list)
#   deepwiki owner/repo 4.1-gpt...   # Fetch a specific subpage
#   deepwiki owner/repo --all        # Fetch all pages concatenated
#   deepwiki owner/repo --save       # Save output to file
#
# Examples:
#   deepwiki karpathy/nanochat
#   deepwiki langchain-ai/langchain 3.1-agent-system
#   deepwiki anthropics/anthropic-sdk-python --toc
#   deepwiki openai/openai-python --all --save

set -euo pipefail

if ! command -v firecrawl &> /dev/null; then
    echo "Error: firecrawl CLI not found. Install with: npm install -g firecrawl-cli" >&2
    exit 1
fi

SAVE_DIR="$HOME/Desktop/Screencaps & Chats/Web-Scrapes"
BASE_URL="https://deepwiki.com"

usage() {
    cat <<'EOF'
Usage: deepwiki <owner/repo> [section] [options]

Fetch AI-generated wiki documentation for any public GitHub repo.

Arguments:
  owner/repo    GitHub repository (e.g., karpathy/nanochat)
  section       Optional section slug (e.g., 4.1-gpt-transformer-implementation)

Options:
  --toc         Show table of contents only (list all available pages)
  --all         Fetch and concatenate all wiki pages
  --save        Save output to ~/Desktop/Screencaps & Chats/Web-Scrapes/
  -o FILE       Save output to specific file
  --help        Show this help

Examples:
  deepwiki karpathy/nanochat                    # Overview page
  deepwiki karpathy/nanochat --toc              # List all sections
  deepwiki karpathy/nanochat 4.1-gpt-transformer-implementation
  deepwiki langchain-ai/langchain --all --save  # Full wiki dump
EOF
    exit 0
}

# Parse arguments
REPO=""
SECTION=""
TOC_ONLY=false
FETCH_ALL=false
SAVE=false
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --toc) TOC_ONLY=true; shift ;;
        --all) FETCH_ALL=true; shift ;;
        --save) SAVE=true; shift ;;
        -o) OUTPUT_FILE="$2"; shift 2 ;;
        *)
            if [[ -z "$REPO" ]]; then
                REPO="$1"
            elif [[ -z "$SECTION" ]]; then
                SECTION="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$REPO" ]]; then
    echo "Error: repository required (e.g., karpathy/nanochat)" >&2
    usage
fi

# Strip leading github.com/ or https://github.com/ if provided
REPO="${REPO#https://github.com/}"
REPO="${REPO#github.com/}"
REPO="${REPO%/}"

# Validate owner/repo format
if [[ ! "$REPO" =~ ^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$ ]]; then
    echo "Error: invalid repo format '$REPO'. Expected: owner/repo" >&2
    exit 1
fi

# Build URL
URL="${BASE_URL}/${REPO}"
if [[ -n "$SECTION" ]]; then
    URL="${URL}/${SECTION}"
fi

# Function to extract TOC from scraped content (macOS-compatible, no grep -P)
extract_toc() {
    # Extract markdown links to deepwiki subpages using sed (works on macOS + Linux)
    sed -n 's/.*\[\([^]]*\)\](https:\/\/deepwiki\.com\/[^)]*).*/\1/p' | \
        while IFS= read -r title; do
            echo "$title"
        done
}

# Function to scrape a single page (warns on empty response)
scrape_page() {
    local page_url="$1"
    local content
    content=$(firecrawl scrape "$page_url" --only-main-content 2>/dev/null) || true

    if [[ -z "${content// /}" ]]; then
        echo "Warning: No content found at $page_url" >&2
        echo "DeepWiki may not have indexed this repository yet." >&2
        return 1
    fi

    echo "$content"
}

# Determine output destination
output() {
    if [[ -n "$OUTPUT_FILE" ]]; then
        cat > "$OUTPUT_FILE"
        echo "Saved to: $OUTPUT_FILE" >&2
    elif [[ "$SAVE" == true ]]; then
        local filename
        filename="deepwiki-$(echo "$REPO" | tr '/' '-')"
        [[ -n "$SECTION" ]] && filename="${filename}-${SECTION}"
        filename="${filename}.md"
        local path="${SAVE_DIR}/${filename}"
        mkdir -p "$SAVE_DIR"
        cat > "$path"
        echo "Saved to: $path" >&2
    else
        cat
    fi
}

if [[ "$TOC_ONLY" == true ]]; then
    # Fetch overview page and extract just the TOC
    echo "# DeepWiki: ${REPO}" >&2
    echo "Fetching table of contents..." >&2
    scrape_page "$URL" | extract_toc | output

elif [[ "$FETCH_ALL" == true ]]; then
    # First get the TOC to find all page URLs
    echo "# DeepWiki: ${REPO}" >&2
    echo "Fetching table of contents..." >&2
    overview=$(scrape_page "$URL")

    # Extract page URLs from overview (macOS-compatible, escape dots in repo name)
    REPO_ESCAPED=$(echo "$REPO" | sed 's/[.]/\\./g')
    pages=$(echo "$overview" | sed -n "s|.*\(https://deepwiki\.com/${REPO_ESCAPED}/[0-9][^)\"]*\).*|\1|p" | sort -t/ -k6 -V | uniq)

    if [[ -z "$pages" ]]; then
        echo "No subpages found. Outputting overview only." >&2
        echo "$overview" | output
        exit 0
    fi

    page_count=$(echo "$pages" | wc -l | tr -d ' ')
    echo "Found ${page_count} pages. Fetching all..." >&2

    # Concatenate all pages
    {
        echo "# DeepWiki: ${REPO}"
        echo ""
        echo "---"
        echo ""

        i=0
        while IFS= read -r page_url; do
            i=$((i + 1))
            slug="${page_url#${BASE_URL}/${REPO}/}"
            echo "Fetching [${i}/${page_count}]: ${slug}..." >&2
            echo ""
            echo "---"
            echo ""
            scrape_page "$page_url"
            echo ""
        done <<< "$pages"
    } | output

    echo "Done. Fetched ${page_count} pages." >&2

else
    # Single page fetch
    if [[ -n "$SECTION" ]]; then
        echo "Fetching: ${REPO}/${SECTION}" >&2
    else
        echo "Fetching overview: ${REPO}" >&2
    fi
    scrape_page "$URL" | output
fi
