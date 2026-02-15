#!/usr/bin/env python3
"""
RLAMA Retrieve — Return raw chunks or synthesize via external LLM.

Bypasses local LLM generation. Reads RLAMA's chunk store,
embeds the query via Ollama, and returns top-K chunks by cosine similarity.
Optionally synthesizes an answer via OpenRouter, TogetherAI, or any
OpenAI-compatible endpoint.

First run builds an embedding cache (~30s for 3K chunks).
Subsequent queries are <1s.

Usage:
    python3 rlama_retrieve.py <rag-name> "your query"
    python3 rlama_retrieve.py <rag-name> "your query" -k 20 --json
    python3 rlama_retrieve.py <rag-name> "your query" --synthesize
    python3 rlama_retrieve.py <rag-name> "your query" --synthesize --synth-model anthropic/claude-sonnet-4
    python3 rlama_retrieve.py <rag-name> "your query" --synthesize --provider togetherai
    python3 rlama_retrieve.py <rag-name> "your query" --synthesize --endpoint https://my-api.com/v1/chat/completions
    python3 rlama_retrieve.py <rag-name> "your query" --rebuild-cache
    python3 rlama_retrieve.py --list
"""

import argparse
import json
import math
import os
import sys
import time
import urllib.request
import urllib.error

RLAMA_DIR = os.path.expanduser("~/.rlama")
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_EMBED_MODEL = "nomic-embed-text"
CACHE_FILENAME = "claude_cache.json"
BATCH_SIZE = 50  # chunks per embedding request


def load_chunks(rag_name: str) -> list[dict]:
    """Load chunks from RLAMA's info.json."""
    info_path = os.path.join(RLAMA_DIR, rag_name, "info.json")
    if not os.path.exists(info_path):
        raise FileNotFoundError(f"RAG '{rag_name}' not found at {info_path}")

    with open(info_path) as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    if not chunks:
        raise ValueError(f"RAG '{rag_name}' has no chunks")

    return [
        {
            "id": c["id"],
            "content": c["content"],
            "document_id": c.get("documentId", ""),
            "chunk_index": c.get("chunk_index", c.get("chunkNumber", 0)),
            "metadata": c.get("metadata", {}),
        }
        for c in chunks
        if c.get("content", "").strip()
    ]


def get_info_mtime(rag_name: str) -> float:
    """Get modification time of info.json."""
    info_path = os.path.join(RLAMA_DIR, rag_name, "info.json")
    return os.path.getmtime(info_path)


def embed_texts(texts: list[str], model: str = DEFAULT_EMBED_MODEL) -> list[list[float]]:
    """Embed texts via Ollama API. Batches automatically."""
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        payload = json.dumps({"model": model, "input": batch}).encode()

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach Ollama at {OLLAMA_URL}. Is it running? Error: {e}"
            )

        embeddings = result.get("embeddings", [])
        if len(embeddings) != len(batch):
            raise ValueError(
                f"Expected {len(batch)} embeddings, got {len(embeddings)}"
            )

        all_embeddings.extend(embeddings)

        if i + BATCH_SIZE < len(texts):
            done = min(i + BATCH_SIZE, len(texts))
            print(f"  Embedded {done}/{len(texts)} chunks...", file=sys.stderr)

    return all_embeddings


def l2_normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector for cosine similarity via dot product."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def dot_product(a: list[float], b: list[float]) -> float:
    """Dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def build_cache(rag_name: str, chunks: list[dict], model: str = DEFAULT_EMBED_MODEL) -> dict:
    """Build embedding cache for a RAG's chunks."""
    print(f"Building embedding cache for '{rag_name}' ({len(chunks)} chunks)...", file=sys.stderr)
    start = time.time()

    texts = [c["content"] for c in chunks]
    raw_embeddings = embed_texts(texts, model)

    # Pre-normalize for fast cosine similarity
    normalized = [l2_normalize(e) for e in raw_embeddings]

    cache = {
        "model": model,
        "chunk_count": len(chunks),
        "info_mtime": get_info_mtime(rag_name),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "embeddings": normalized,
        "chunk_ids": [c["id"] for c in chunks],
    }

    cache_path = os.path.join(RLAMA_DIR, rag_name, CACHE_FILENAME)
    with open(cache_path, "w") as f:
        json.dump(cache, f)

    elapsed = time.time() - start
    size_mb = os.path.getsize(cache_path) / (1024 * 1024)
    print(
        f"Cache built: {len(chunks)} embeddings, {size_mb:.1f}MB, {elapsed:.1f}s",
        file=sys.stderr,
    )

    return cache


def load_or_build_cache(
    rag_name: str, chunks: list[dict], model: str = DEFAULT_EMBED_MODEL, force_rebuild: bool = False
) -> dict:
    """Load cache if valid, rebuild if stale or missing."""
    cache_path = os.path.join(RLAMA_DIR, rag_name, CACHE_FILENAME)

    if not force_rebuild and os.path.exists(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)

        current_mtime = get_info_mtime(rag_name)
        if (
            cache.get("chunk_count") == len(chunks)
            and cache.get("info_mtime") == current_mtime
            and cache.get("model") == model
            and len(cache.get("embeddings", [])) == len(chunks)
        ):
            return cache

        print("Cache stale (chunks or info.json changed). Rebuilding...", file=sys.stderr)

    return build_cache(rag_name, chunks, model)


def retrieve(
    rag_name: str,
    query: str,
    top_k: int = 10,
    model: str = DEFAULT_EMBED_MODEL,
    force_rebuild: bool = False,
) -> dict:
    """Retrieve top-K chunks by cosine similarity to query."""
    chunks = load_chunks(rag_name)
    cache = load_or_build_cache(rag_name, chunks, model, force_rebuild)

    cache_status = "rebuilt" if force_rebuild else "hit"
    if not os.path.exists(os.path.join(RLAMA_DIR, rag_name, CACHE_FILENAME)):
        cache_status = "built"

    # Embed query
    query_embedding = l2_normalize(embed_texts([query], model)[0])

    # Score all chunks
    scores = []
    for i, chunk_emb in enumerate(cache["embeddings"]):
        score = dot_product(query_embedding, chunk_emb)
        scores.append((score, i))

    # Sort by score descending
    scores.sort(key=lambda x: x[0], reverse=True)

    # Build results
    results = []
    for rank, (score, idx) in enumerate(scores[:top_k], 1):
        chunk = chunks[idx]
        results.append(
            {
                "rank": rank,
                "score": round(score, 4),
                "content": chunk["content"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "metadata": chunk["metadata"],
            }
        )

    return {
        "query": query,
        "rag_name": rag_name,
        "results": results,
        "total_chunks": len(chunks),
        "cache_status": cache_status,
        "embed_model": model,
        "error": None,
    }


def synthesize(query: str, chunks: list[dict], model: str = None,
               provider: str = None, endpoint: str = None) -> dict:
    """Synthesize an answer from retrieved chunks using an external LLM provider.

    Providers: openrouter, togetherai, or a custom endpoint (any OpenAI-compatible API).

    Detection order:
    1. Explicit --endpoint URL (uses provided API key via --synth-key or env)
    2. Explicit --provider flag
    3. Auto-detect from model name (contains / → openrouter, otherwise togetherai)
    4. Auto-detect from available API keys (OPENROUTER_API_KEY, TOGETHER_API_KEY)
    """
    providers = {
        "openrouter": {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key_env": "OPENROUTER_API_KEY",
            "default_model": "anthropic/claude-sonnet-4",
        },
        "togetherai": {
            "url": "https://api.together.xyz/v1/chat/completions",
            "key_env": "TOGETHER_API_KEY",
            "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        },
        "ollama": {
            "url": f"{OLLAMA_URL}/v1/chat/completions",
            "key_env": None,  # No API key needed for local Ollama
            "default_model": "qwen2.5:7b",
        },
    }

    # Custom endpoint overrides everything
    if endpoint:
        api_key = os.environ.get("SYNTH_API_KEY", "")
        if not api_key:
            return {"error": "Custom endpoint requires SYNTH_API_KEY env var.", "answer": None}
        url = endpoint
        if not model:
            model = "default"
        provider = "custom"
    else:
        # Detect provider
        if not provider:
            if model and "/" in model:
                provider = "openrouter"
            elif model:
                provider = "togetherai"

        if not provider:
            for p, cfg in providers.items():
                if os.environ.get(cfg["key_env"]):
                    provider = p
                    break

        if not provider:
            return {"error": "No API key found. Set OPENROUTER_API_KEY or TOGETHER_API_KEY.", "answer": None}

        if provider not in providers:
            return {"error": f"Unknown provider '{provider}'. Use: openrouter, togetherai, ollama, or --endpoint URL.", "answer": None}

        cfg = providers[provider]
        if cfg["key_env"]:
            api_key = os.environ.get(cfg["key_env"])
            if not api_key:
                return {"error": f"Provider '{provider}' selected but {cfg['key_env']} not set.", "answer": None}
        else:
            api_key = "ollama"  # Ollama doesn't need auth but the header is required

        url = cfg["url"]
        if not model:
            model = cfg["default_model"]

    # Build context from chunks with metadata
    context_parts = []
    for c in chunks:
        header = f"[{c['document_id']} chunk {c['chunk_index']}] (score: {c.get('score', 'N/A')})"
        context_parts.append(f"{header}\n{c['content']}")
    context = "\n\n---\n\n".join(context_parts)

    # Use a lighter prompt for small local models (ollama) — strict grounding
    # rules cause 7B models to over-hedge rather than synthesize.
    # Prompt V3: structured output + anti-hedge + category awareness
    if provider == "ollama":
        system_prompt = (
            "You are a research assistant. Answer questions using ONLY the CONTEXT documents below.\n\n"
            "FORMAT:\n"
            "1. Start with a direct 1-sentence answer summarizing the key finding.\n"
            "2. List specific details as bullet points with citations [document_name].\n"
            "3. End with a brief summary connecting the details.\n\n"
            "RULES:\n"
            "- Extract specific names, tools, topics, and examples from the documents.\n"
            "- When a document header describes its domain (e.g., 'AI coding tools, agent patterns, "
            "Claude Code techniques, skill development'), use those domain keywords in your answer.\n"
            "- When a document says it has N entries, describe the themes and specific items visible.\n"
            "- Cite sources as [document_name].\n"
            "- NEVER say 'insufficient information', 'no specific mention', or 'does not contain'. "
            "Instead, describe what the documents DO contain that is relevant."
        )
    else:
        system_prompt = (
            "You are an expert assistant. Your responses must be grounded STRICTLY in the provided context documents.\n\n"
            "RULES:\n"
            "1. Use ONLY information explicitly stated in the CONTEXT below. Do not use prior knowledge.\n"
            "2. Every factual claim MUST include a citation: [document_name chunk N].\n"
            "3. When multiple sources agree, cite all relevant chunks.\n"
            "4. When sources conflict, acknowledge: \"Source [X] states A, while [Y] states B.\"\n"
            "5. If the CONTEXT does not contain sufficient information, respond: "
            "\"The provided documents do not contain enough information to answer this question. "
            "Specifically, [what is missing].\"\n"
            "6. Do not speculate, infer, or assume beyond what is explicitly stated.\n"
            "7. Synthesize across sources when relevant—combine evidence into a coherent answer."
        )

    user_message = f"Question: {query}\n\nCONTEXT:\n\n{context}"

    # All providers use OpenAI-compatible format
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/rlama/rlama"

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())

        answer = result["choices"][0]["message"]["content"]

        return {
            "answer": answer,
            "model": model,
            "provider": provider,
            "error": None,
        }

    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"API error {e.code}: {body[:500]}", "answer": None}
    except Exception as e:
        return {"error": str(e), "answer": None}


def list_rags() -> list[str]:
    """List available RAG systems."""
    if not os.path.exists(RLAMA_DIR):
        return []
    rags = []
    for name in sorted(os.listdir(RLAMA_DIR)):
        info_path = os.path.join(RLAMA_DIR, name, "info.json")
        if os.path.isfile(info_path):
            rags.append(name)
    return rags


def format_human(result: dict) -> str:
    """Format results for human reading."""
    lines = []
    lines.append(
        f'=== Retrieved {len(result["results"])} chunks for: "{result["query"]}" ==='
    )
    lines.append(
        f'    RAG: {result["rag_name"]} ({result["total_chunks"]} total chunks, cache: {result["cache_status"]})'
    )
    lines.append("")

    for r in result["results"]:
        content_preview = r["content"][:500]
        if len(r["content"]) > 500:
            content_preview += "..."
        lines.append(
            f'[{r["rank"]}] (score: {r["score"]:.3f}) {r["document_id"]} chunk {r["chunk_index"]}'
        )
        lines.append(content_preview)
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve raw chunks from RLAMA RAG (no LLM generation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s twitter-idaeandaktyl "What Claude Code techniques has Tom bookmarked?"
  %(prog)s my-docs "explain the architecture" -k 20 --json
  %(prog)s my-docs "query" --synthesize
  %(prog)s my-docs "query" --synthesize --synth-model anthropic/claude-sonnet-4
  %(prog)s my-docs "query" --synthesize --provider togetherai
  %(prog)s my-docs "query" --synthesize --endpoint https://my-api.com/v1/chat/completions
  %(prog)s my-docs "query" --rebuild-cache
  %(prog)s --list
""",
    )

    parser.add_argument("rag_name", nargs="?", help="Name of the RAG to retrieve from")
    parser.add_argument("query", nargs="?", help="Search query")

    parser.add_argument(
        "-k", "--top-k", type=int, default=10, help="Number of chunks to retrieve (default: 10)"
    )
    parser.add_argument(
        "--model",
        "-m",
        default=DEFAULT_EMBED_MODEL,
        help=f"Embedding model (default: {DEFAULT_EMBED_MODEL})",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--rebuild-cache", action="store_true", help="Force rebuild embedding cache"
    )
    parser.add_argument("--list", "-l", action="store_true", help="List available RAGs")

    # Synthesis options
    parser.add_argument(
        "--synthesize", "-s", action="store_true",
        help="Synthesize answer from retrieved chunks via external LLM",
    )
    parser.add_argument(
        "--synth-model", default=None,
        help="Model for synthesis (e.g., anthropic/claude-sonnet-4, meta-llama/Llama-3.3-70B-Instruct-Turbo)",
    )
    parser.add_argument(
        "--provider", default=None, choices=["openrouter", "togetherai", "ollama"],
        help="LLM provider for synthesis (auto-detected from model name or API keys)",
    )
    parser.add_argument(
        "--endpoint", default=None,
        help="Custom OpenAI-compatible endpoint URL (requires SYNTH_API_KEY env var)",
    )

    args = parser.parse_args()

    if args.list:
        rags = list_rags()
        if not rags:
            print("No RAG systems found in ~/.rlama/")
        else:
            for r in rags:
                info_path = os.path.join(RLAMA_DIR, r, "info.json")
                with open(info_path) as f:
                    data = json.load(f)
                chunk_count = len(data.get("chunks", []))
                cache_path = os.path.join(RLAMA_DIR, r, CACHE_FILENAME)
                cached = "cached" if os.path.exists(cache_path) else "no cache"
                print(f"  {r} ({chunk_count} chunks, {cached})")
        return

    if not args.rag_name:
        parser.error("rag_name is required (or use --list)")
    if not args.query:
        parser.error("query is required")

    try:
        result = retrieve(
            rag_name=args.rag_name,
            query=args.query,
            top_k=args.top_k,
            model=args.model,
            force_rebuild=args.rebuild_cache,
        )
    except (FileNotFoundError, ValueError, ConnectionError) as e:
        error_result = {"error": str(e), "query": args.query, "rag_name": args.rag_name, "results": []}
        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Synthesize if requested
    if args.synthesize:
        print(f"Synthesizing via external LLM...", file=sys.stderr)
        synth_result = synthesize(
            query=args.query,
            chunks=result["results"],
            model=args.synth_model,
            provider=args.provider,
            endpoint=args.endpoint,
        )
        result["synthesis"] = synth_result
        if synth_result.get("error"):
            print(f"Synthesis error: {synth_result['error']}", file=sys.stderr)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))
        if args.synthesize and result.get("synthesis", {}).get("answer"):
            synth = result["synthesis"]
            print(f"\n=== Synthesized Answer ({synth['provider']}/{synth['model']}) ===\n")
            print(synth["answer"])
            print()


if __name__ == "__main__":
    main()
