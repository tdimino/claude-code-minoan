#!/usr/bin/env python3
"""
Test OpenAI API connectivity and model availability for GPT Image models.

Usage:
    python test_connection.py                    # Basic connectivity test
    python test_connection.py --check-models     # List available image models
    python test_connection.py --generate-test    # Generate a tiny test image
    python test_connection.py --json             # JSON output for scripting

Env: OPENAI_API_KEY
"""

import argparse
import json
import os
import sys
import time

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)

IMAGE_MODELS = ["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]


def test_api_key(client: OpenAI) -> dict:
    try:
        models = client.models.list()
        return {"status": "ok", "models_accessible": True}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_models(client: OpenAI) -> list[dict]:
    results = []
    try:
        available = {m.id for m in client.models.list()}
    except Exception as e:
        return [{"model": m, "available": "unknown", "error": str(e)} for m in IMAGE_MODELS]

    for model_id in IMAGE_MODELS:
        results.append({
            "model": model_id,
            "available": model_id in available,
        })
    return results


def generate_test(client: OpenAI) -> dict:
    start = time.time()
    try:
        response = client.images.generate(
            model="gpt-image-2",
            prompt="A small red circle on a white background",
            size="1024x1024",
            quality="low",
            n=1,
            output_format="png",
        )
        elapsed = time.time() - start
        has_image = bool(response.data and response.data[0].b64_json)
        return {
            "status": "ok",
            "model": "gpt-image-2",
            "has_image": has_image,
            "elapsed_seconds": round(elapsed, 2),
        }
    except Exception as e:
        elapsed = time.time() - start
        error_msg = str(e)
        fallback_triggers = ("not found", "does not exist", "must be verified", "verification_required")
        if "gpt-image-2" in error_msg and any(t in error_msg.lower() for t in fallback_triggers):
            try:
                response = client.images.generate(
                    model="gpt-image-1.5",
                    prompt="A small red circle on a white background",
                    size="1024x1024",
                    quality="low",
                    n=1,
                    output_format="png",
                )
                elapsed = time.time() - start
                return {
                    "status": "ok",
                    "model": "gpt-image-1.5",
                    "note": "gpt-image-2 not yet available, fell back to gpt-image-1.5",
                    "has_image": bool(response.data and response.data[0].b64_json),
                    "elapsed_seconds": round(elapsed, 2),
                }
            except Exception as e2:
                return {"status": "error", "error": str(e2), "elapsed_seconds": round(elapsed, 2)}
        return {"status": "error", "error": error_msg, "elapsed_seconds": round(elapsed, 2)}


def main():
    parser = argparse.ArgumentParser(description="Test GPT Image API connectivity")
    parser.add_argument("--check-models", action="store_true", help="List available image models")
    parser.add_argument("--generate-test", action="store_true", help="Generate a test image")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--api-key", help="API key override")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        result = {"status": "error", "error": "OPENAI_API_KEY not set"}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    results = {}

    results["api"] = test_api_key(client)

    if args.check_models:
        results["models"] = check_models(client)

    if args.generate_test:
        results["generate"] = generate_test(client)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        api = results["api"]
        if api["status"] == "ok":
            print(f"API: OK")
        else:
            print(f"API: FAILED — {api.get('error', 'unknown')}")

        if "models" in results:
            print("\nImage Models:")
            for m in results["models"]:
                status = "available" if m["available"] else "not found"
                print(f"  {m['model']}: {status}")

        if "generate" in results:
            gen = results["generate"]
            if gen["status"] == "ok":
                model = gen.get("model", "gpt-image-2")
                note = f" ({gen['note']})" if "note" in gen else ""
                print(f"\nTest generation: OK ({model}, {gen['elapsed_seconds']}s){note}")
            else:
                print(f"\nTest generation: FAILED — {gen.get('error', 'unknown')}")

    has_errors = any(
        v.get("status") == "error"
        for v in results.values()
        if isinstance(v, dict) and "status" in v
    )
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
