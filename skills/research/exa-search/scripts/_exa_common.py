"""
Shared plumbing for the exa-search scripts: auth, requests, error envelopes,
warnings/notices, cost display, categories, schemas, and legacy-flag mapping.

Source of truth: OpenAPI spec 2.0.0 (exa.ai/docs/exa-spec.yaml), synced 2026-10-19.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, NoReturn, Optional, Tuple

import requests

BASE_URL = "https://api.exa.ai"
DYNAMIC_HIGHLIGHTS_BETA = "dynamic-highlights-2026-08-28"
TIMEOUT = (10, 300)  # connect, read — deep searches and /answer streams run long

# /search category enum (spec 2.0.0). Other strings are sent as category hints.
CATEGORIES = ["company", "publication", "news", "personal site", "financial report", "people"]
CATEGORY_ALIASES = {"research paper": "publication"}
DEPRECATED_CATEGORIES = ["pdf", "github"]
CATEGORY_CHOICES = CATEGORIES + list(CATEGORY_ALIASES) + DEPRECATED_CATEGORIES

VALID_SECTIONS = ["header", "navigation", "banner", "body", "sidebar", "footer", "metadata"]

# Deprecated livecrawl modes → maxAgeHours (contents/quickstart: preferred ≈ 1h).
# "fallback" is the API default behaviour, so it maps to omitting the field.
LIVECRAWL_TO_MAX_AGE = {"always": 0, "preferred": 1, "never": -1, "fallback": None}
LIVECRAWL_CHOICES = list(LIVECRAWL_TO_MAX_AGE)

# Preset output schemas. Object schemas on /search allow at most 10 properties
# in total and 2 levels of nesting; the Agent API has no such limit.
PRESET_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "company": {
        "type": "object",
        "required": ["companies"],
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "description"],
                    "properties": {
                        "name": {"type": "string", "description": "Company name"},
                        "description": {"type": "string", "description": "What the company does"},
                        "ceo": {"type": "string", "description": "Current CEO"},
                        "headquarters": {"type": "string", "description": "HQ location"},
                        "funding": {"type": "string", "description": "Total funding raised"}
                    }
                }
            }
        }
    },
    "paper-survey": {
        "type": "object",
        "required": ["papers"],
        "properties": {
            "papers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "authors", "key_contribution"],
                    "properties": {
                        "title": {"type": "string", "description": "Paper title"},
                        "authors": {"type": "string", "description": "Author names"},
                        "year": {"type": "number", "description": "Publication year"},
                        "key_contribution": {"type": "string", "description": "Main contribution"},
                        "methodology": {"type": "string", "description": "Research methodology"},
                        "findings": {"type": "string", "description": "Key findings"}
                    }
                }
            }
        }
    },
    "competitor-analysis": {
        "type": "object",
        "required": ["competitors"],
        "properties": {
            "competitors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "product"],
                    "properties": {
                        "name": {"type": "string", "description": "Company name"},
                        "product": {"type": "string", "description": "Main product or service"},
                        "market_position": {"type": "string", "description": "Market positioning"},
                        "strengths": {"type": "array", "items": {"type": "string"}, "description": "Key strengths"},
                        "weaknesses": {"type": "array", "items": {"type": "string"}, "description": "Key weaknesses"},
                        "pricing": {"type": "string", "description": "Pricing model or range"}
                    }
                }
            }
        }
    },
    "person": {
        "type": "object",
        "required": ["people"],
        "properties": {
            "people": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "title"],
                    "properties": {
                        "name": {"type": "string", "description": "Full name"},
                        "title": {"type": "string", "description": "Current title or role"},
                        "organization": {"type": "string", "description": "Current organization"},
                        "background": {"type": "string", "description": "Professional background"},
                        "notable_achievements": {"type": "array", "items": {"type": "string"}, "description": "Notable achievements"}
                    }
                }
            }
        }
    },
    "news-digest": {
        "type": "object",
        "required": ["stories"],
        "properties": {
            "stories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["headline", "summary"],
                    "properties": {
                        "headline": {"type": "string", "description": "Story headline"},
                        "source": {"type": "string", "description": "Publication source"},
                        "date": {"type": "string", "description": "Publication date"},
                        "summary": {"type": "string", "description": "Story summary"},
                        "significance": {"type": "string", "description": "Why this matters"}
                    }
                }
            }
        }
    },
}


class ExaAPIError(Exception):
    """An HTTP error from the Exa API, with the server's own message kept verbatim."""

    def __init__(self, status: int, tag: Optional[str], message: str, request_id: Optional[str] = None):
        self.status, self.tag, self.message, self.request_id = status, tag, message, request_id
        prefix = f"network error ({tag})" if status == 0 else f"HTTP {status}{' ' + tag if tag else ''}"
        super().__init__(f"{prefix}: {message}")


# --- requests ---------------------------------------------------------------

def headers(betas: Iterable[str] = ()) -> Dict[str, str]:
    """Auth headers; adds Exa-Beta when beta features are requested."""
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise ValueError("EXA_API_KEY environment variable not set. Get your key at https://dashboard.exa.ai")
    h = {"Content-Type": "application/json", "x-api-key": key}
    betas = list(betas)
    if betas:
        h["Exa-Beta"] = ",".join(betas)
    return h


def _detail_text(detail: Any) -> str:
    """Flatten an agent error `detail` (a JSON string of validation issues)."""
    if isinstance(detail, str):
        try:
            detail = json.loads(detail)
        except ValueError:
            return detail
    if isinstance(detail, list):
        parts = []
        for issue in detail:
            if isinstance(issue, dict):
                path = ".".join(str(p) for p in issue.get("path") or [])
                parts.append(f"{path}: {issue.get('message')}" if path else str(issue.get("message")))
            else:
                parts.append(str(issue))
        return "; ".join(parts)
    return json.dumps(detail)


def api_error(response) -> ExaAPIError:
    """Parse either error envelope into an ExaAPIError.

    Search/contents/answer: {"error": "text", "tag": "TAG", "requestId": ...}
    Agent:                  {"error": {"type", "code", "message", "detail"?}, "requestId": ...}
    """
    try:
        body = response.json()
    except ValueError:
        return ExaAPIError(response.status_code, None, response.text[:1000])
    if not isinstance(body, dict):
        return ExaAPIError(response.status_code, None, str(body)[:1000])
    err = body.get("error")
    request_id = body.get("requestId") or _header_request_id(response)
    if isinstance(err, dict):
        message = err.get("message", "")
        if err.get("detail"):
            message = f"{message} ({_detail_text(err['detail'])})"
        return ExaAPIError(response.status_code, err.get("code") or err.get("type"), message, request_id)
    return ExaAPIError(response.status_code, body.get("tag"), str(err or body), request_id)


def _header_request_id(response) -> Optional[str]:
    return (getattr(response, "headers", None) or {}).get("x-request-id")


def _send(method: str, path: str, betas: Iterable[str] = (), **kwargs):
    """One request. Network failures and non-JSON success bodies become ExaAPIError (status 0 / INVALID_JSON)."""
    send = requests.post if method == "POST" else requests.get
    try:
        response = send(f"{BASE_URL}{path}", headers=headers(betas), timeout=TIMEOUT, **kwargs)
    except requests.exceptions.RequestException as e:
        raise ExaAPIError(0, type(e).__name__, str(e)) from e
    if response.status_code >= 400:
        raise api_error(response)
    return response


def _json(response) -> Dict[str, Any]:
    try:
        return response.json()
    except ValueError:
        raise ExaAPIError(response.status_code, "INVALID_JSON", (response.text or "")[:500],
                          _header_request_id(response))


def post(path: str, payload: Dict[str, Any], betas: Iterable[str] = (), stream: bool = False):
    """POST to the API. Returns parsed JSON, or the raw Response when streaming."""
    response = _send("POST", path, betas, json=payload, stream=stream)
    return response if stream else _json(response)


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _json(_send("GET", path, params=params))


# --- response display -------------------------------------------------------

def report_warnings(results: Dict[str, Any]) -> None:
    """Warnings describe the request (ignored or deprecated fields): log to stderr."""
    for w in results.get("warnings") or []:
        print(f"Warning [{w.get('code', '?')}] {w.get('message', w)}", file=sys.stderr)


def format_notices(results: Dict[str, Any]) -> List[str]:
    """Notices describe how results were produced (e.g. RESTRICTIONS_RELAXED): show them with the results."""
    lines = []
    for n in results.get("notices") or []:
        lines.append(f"NOTICE [{n.get('code', '?')}]: {n.get('message', n)}")
    return lines


def format_cost(cost: Optional[Dict[str, Any]]) -> List[str]:
    """Render costDollars: `total` plus any nested breakdown (search/contents/summary, or agent fields)."""
    if not isinstance(cost, dict):
        return [f"\n{'=' * 60}", f"COST: ${cost:.4f}"] if isinstance(cost, (int, float)) else []
    lines = [f"\n{'=' * 60}", f"COST: ${cost.get('total') or 0:.4f}"]
    for key, val in cost.items():
        if key == "total":
            continue
        if isinstance(val, dict):
            for sub, amount in val.items():
                if isinstance(amount, (int, float)):
                    lines.append(f"  {key}.{sub}: ${amount:.4f}")
        elif isinstance(val, (int, float)) and val:
            lines.append(f"  {key}: ${val:.4f}")
    return lines


def format_grounding(grounding: Optional[List[Dict[str, Any]]]) -> List[str]:
    """Field-level citations from outputSchema (/search) or Agent runs."""
    if not grounding:
        return []
    lines = [f"\n{'=' * 60}", f"GROUNDING ({len(grounding)} fields cited):", "-" * 40]
    for g in grounding:
        indicator = {"high": "[H]", "medium": "[M]", "low": "[L]"}.get(g.get("confidence"), "[?]")
        lines.append(f"\n  {indicator} {g.get('field', 'unknown')}")
        for c in g.get("citations") or []:
            lines.append(f"      -> {(c.get('title') or 'No title')[:60]}")
            lines.append(f"         {c.get('url', '')}")
    return lines


# --- argument helpers -------------------------------------------------------

def legacy(flag: str, hint: str) -> None:
    """One stderr line for a flag kept only for backward compatibility."""
    print(f"Note: {flag} is legacy; {hint}", file=sys.stderr)


def note(message: str) -> None:
    """One stderr line for a valid flag that does nothing in this context."""
    print(f"Note: {message}", file=sys.stderr)


# --- content options shared by /search, /contents, /findSimilar --------------

def text_option(max_chars: Optional[int] = None, verbosity: Optional[str] = None,
                include_sections: Optional[List[str]] = None, exclude_sections: Optional[List[str]] = None,
                html: bool = False) -> Any:
    config: Dict[str, Any] = {}
    if max_chars:
        config["maxCharacters"] = max_chars
    if html:
        config["includeHtmlTags"] = True
    if verbosity:
        config["verbosity"] = verbosity
    if include_sections:
        config["includeSections"] = include_sections
    if exclude_sections:
        config["excludeSections"] = exclude_sections
    return config or True


def highlights_option(enabled: bool = False, query: Optional[str] = None, max_chars: Optional[int] = None,
                      dynamic: bool = False) -> Tuple[Any, List[str]]:
    """Returns (highlights value or None, beta flags). Any highlight option implies highlights."""
    if dynamic and max_chars:
        raise ValueError("--dynamic is not compatible with --highlights-max-chars")
    if not (enabled or query or max_chars or dynamic):
        return None, []
    config: Dict[str, Any] = {}
    betas: List[str] = []
    if dynamic:
        config["dynamic"] = True
        betas.append(DYNAMIC_HIGHLIGHTS_BETA)
    if query:
        config["query"] = query
    if max_chars:
        config["maxCharacters"] = max_chars
    return config or True, betas


def extras_option(links: int = 0, images: int = 0) -> Optional[Dict[str, int]]:
    extras = {}
    if links > 0:
        extras["links"] = links
    if images > 0:
        extras["imageLinks"] = images
    return extras or None


def context_option(enabled: bool, max_chars: Optional[int] = None) -> Any:
    if not enabled:
        return None
    legacy("--context", "Exa deprecated contents.context; prefer --highlights or --max-chars.")
    return {"maxCharacters": max_chars} if max_chars else True


def check_snapshot(snapshot_as_of: Optional[str], max_age_hours: Optional[int], livecrawl: Optional[str],
                   subpages: int = 0, timeout: Optional[int] = None) -> None:
    if snapshot_as_of and (max_age_hours is not None or livecrawl or subpages or timeout):
        raise ValueError("--snapshot-as-of cannot be combined with --max-age-hours, --livecrawl, --timeout, "
                         "or --subpages")


class _ExtendCommaSplit(argparse.Action):
    """`--domains a.com,b.com --domains c.com` → [a.com, b.com, c.com]."""

    def __call__(self, parser, namespace, values, option_string=None):
        items = list(getattr(namespace, self.dest, None) or [])
        items += [v.strip() for value in values for v in value.split(",") if v.strip()]
        setattr(namespace, self.dest, items)


def add_list_arg(parser: argparse.ArgumentParser, *names: str, split_commas: bool = False, **kwargs) -> None:
    """List flag that accumulates across repeats (`--domains a --domains b` → [a, b])."""
    parser.add_argument(*names, nargs="+", action=_ExtendCommaSplit if split_commas else "extend", **kwargs)


def resolve_category(category: Optional[str]) -> Optional[str]:
    if not category:
        return None
    if category in CATEGORY_ALIASES:
        new = CATEGORY_ALIASES[category]
        legacy(f"--category '{category}'", f"sent as '{new}'.")
        return new
    if category in DEPRECATED_CATEGORIES:
        legacy(f"--category '{category}'", "Exa deprecated it; it is sent as a soft category hint.")
        return category
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Must be one of: {CATEGORIES}")
    return category


def resolve_max_age(max_age_hours: Optional[int], livecrawl: Optional[str], lite: bool = False) -> Optional[int]:
    """--max-age-hours wins; otherwise map deprecated --livecrawl. Lite is cache-only, so no mapping."""
    if max_age_hours is not None:
        return max_age_hours
    if not livecrawl:
        return None
    if lite:
        legacy("--livecrawl", "dropped under --lite (cache-only).")
        return None
    mapped = LIVECRAWL_TO_MAX_AGE[livecrawl]
    legacy("--livecrawl", f"use --max-age-hours ({livecrawl} → "
                          f"{'omitted' if mapped is None else mapped}).")
    return mapped


def date_bound(value: Optional[str], end: bool = False) -> Optional[str]:
    """YYYY-MM-DD → full-day ISO bound; full ISO timestamps pass through."""
    if not value or "T" in value:
        return value
    return f"{value}T23:59:59.999Z" if end else f"{value}T00:00:00.000Z"


def parse_location(value: Optional[str]):
    """`US`, `40.7,-74.0`, or `US,40.7,-74.0` → userLocation string or object."""
    if not value:
        return None
    parts = [p.strip() for p in value.split(",")]
    if len(parts) == 1:
        return value
    try:
        if len(parts) == 2:
            return {"latitude": float(parts[0]), "longitude": float(parts[1])}
        if len(parts) == 3:
            return {"country": parts[0], "latitude": float(parts[1]), "longitude": float(parts[2])}
    except ValueError:
        pass
    raise ValueError(f"Invalid --location '{value}'. Use US, LAT,LON, or US,LAT,LON")


def load_schema(output_schema: Optional[str] = None, schema_file: Optional[str] = None,
                preset: Optional[str] = None, text_output: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Resolve the mutually exclusive schema flags to one schema dict."""
    if output_schema:
        try:
            return json.loads(output_schema)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in --output-schema: {e}")
    if schema_file:
        try:
            with open(schema_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load schema file: {e}")
    if preset:
        return PRESET_SCHEMAS[preset]
    if text_output:
        return {"type": "text", "description": text_output}
    return None


def add_schema_args(parser: argparse.ArgumentParser, text_output: bool = True) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output-schema", help="JSON schema string for structured output")
    group.add_argument("--schema-file", help="Path to JSON file containing output schema")
    group.add_argument("--schema-preset", choices=list(PRESET_SCHEMAS),
                       help="Preset schema: " + ", ".join(PRESET_SCHEMAS))
    if text_output:
        group.add_argument("--text-output", help="Plain-text synthesized answer (description string)")


def die(error: Exception, hint: Optional[str] = None) -> NoReturn:
    """Print an error (plus an optional hint) to stderr and exit 1."""
    if isinstance(error, ExaAPIError):
        print(f"API Error: {error}", file=sys.stderr)
        if error.request_id:
            print(f"Request ID: {error.request_id}", file=sys.stderr)
    else:
        print(f"Error: {error}", file=sys.stderr)
    if hint:
        print(f"Hint: {hint}", file=sys.stderr)
    sys.exit(1)
