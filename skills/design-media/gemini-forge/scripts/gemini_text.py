#!/usr/bin/env python3
"""
Gemini Forge Text Generation Client

Shared library for calling Gemini 3.1 Pro for text-only generation (code, specs, SVG).
Mirrors the REST pattern from nano-banana-pro's gemini_images.py but targets the
text-only reasoning model with thinking support.

Usage:
    from gemini_text import GeminiForgeClient

    client = GeminiForgeClient()
    response = client.generate("Build a React dashboard")
    client.save_code(response, "./output", "dashboard")

    # With screenshot input
    response = client.generate_with_image("Describe this UI", "screenshot.png")

    # Test connection
    python gemini_text.py --test

Environment:
    GEMINI_API_KEY - API key for authentication (same as nano-banana-pro)
"""

import json
import os
import re
import sys
import time
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import requests
except ImportError:
    print("Requires requests library. Install: uv pip install requests", file=sys.stderr)
    sys.exit(1)


# Thinking budget presets
THINKING_BUDGETS = {
    "low": 1024,
    "medium": 8192,
    "high": 32768,
}


class GeminiForgeClient:
    """
    Client for Gemini 3.1 Pro text generation.

    Uses the REST API directly (not SDK) for consistency with nano-banana-pro
    and maximum control over thinking configuration.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemini-3.1-pro-preview"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "API key required. Set GEMINI_API_KEY or pass api_key parameter.\n"
                "Get your key at: https://aistudio.google.com/apikey"
            )
        self.endpoint = f"{self.BASE_URL}/{self.MODEL}:generateContent"

    def _encode_image(self, image_path: Union[str, Path]) -> tuple:
        """Encode image file to base64 for multimodal input (screenshot-to-code)."""
        image_path = Path(image_path)
        ext_to_mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        mime_type = ext_to_mime.get(image_path.suffix.lower(), "image/png")

        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        return image_base64, mime_type

    def _make_request(
        self,
        parts: List[Dict[str, Any]],
        thinking: str = "medium",
        temperature: float = 1.0,
        max_output_tokens: int = 65536,
        system_instruction: Optional[str] = None,
        timeout: int = 300,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Make API request to Gemini 3.1 Pro.

        Args:
            parts: Content parts (text and/or images)
            thinking: Thinking level (low/medium/high) or integer budget
            temperature: Sampling temperature (1.0 recommended with thinking)
            max_output_tokens: Maximum output tokens (up to 65536)
            system_instruction: Optional system prompt
            timeout: Request timeout in seconds
            max_retries: Max retries on 429/5xx errors

        Returns:
            API response dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        # Resolve thinking budget
        if isinstance(thinking, str):
            budget = THINKING_BUDGETS.get(thinking, THINKING_BUDGETS["medium"])
        else:
            budget = int(thinking)

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT"],
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
                "thinkingConfig": {"thinkingBudget": budget},
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Exponential backoff for rate limits
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else None

                # Retry on rate limit or server errors
                if status in (429, 500, 502, 503) and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  Retrying in {wait}s (HTTP {status})...", file=sys.stderr)
                    time.sleep(wait)
                    continue

                error_detail = ""
                try:
                    error_data = e.response.json()
                    error_detail = json.dumps(error_data, indent=2)
                except Exception:
                    error_detail = e.response.text if e.response else str(e)

                raise Exception(f"API request failed (HTTP {status}): {e}\n{error_detail}")

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  Network error, retrying in {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                raise Exception(f"Network error: {e}")

        raise Exception("Max retries exceeded")

    def extract_text(self, response: Dict[str, Any]) -> str:
        """
        Extract text from API response, filtering out thinking parts.

        Returns concatenated text from all non-thought parts.
        """
        candidates = response.get("candidates", [])
        if not candidates:
            raise Exception("No candidates in response")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = []

        for part in parts:
            # Skip thinking/thought parts
            if part.get("thought"):
                continue
            if "text" in part:
                text_parts.append(part["text"])

        return "\n".join(text_parts)

    def generate(
        self,
        prompt: str,
        thinking: str = "medium",
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate text from a prompt."""
        parts = [{"text": prompt}]
        return self._make_request(
            parts,
            thinking=thinking,
            system_instruction=system_instruction,
        )

    def generate_with_image(
        self,
        prompt: str,
        image_path: Union[str, Path],
        thinking: str = "medium",
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate text from a prompt with an image input (screenshot-to-code)."""
        image_data, mime_type = self._encode_image(image_path)

        parts = [
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": image_data,
                }
            },
            {"text": prompt},
        ]

        return self._make_request(
            parts,
            thinking=thinking,
            system_instruction=system_instruction,
        )

    def save_code(
        self,
        response: Dict[str, Any],
        output_dir: Union[str, Path],
        filename: str,
        extension: Optional[str] = None,
    ) -> List[str]:
        """
        Save code from API response to files.

        If the response contains multi-file markers (// --- FILE: path ---),
        splits into individual files. Otherwise saves as a single file.

        Returns list of saved file paths.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        text = self.extract_text(response)
        saved = []

        # Check for multi-file markers
        file_pattern = re.compile(r'^//\s*---\s*FILE:\s*(.+?)\s*---\s*$', re.MULTILINE)
        file_markers = list(file_pattern.finditer(text))

        if file_markers:
            # Multi-file output
            resolved_output = output_dir.resolve()
            for i, match in enumerate(file_markers):
                file_path = match.group(1).strip()
                start = match.end()
                end = file_markers[i + 1].start() if i + 1 < len(file_markers) else len(text)

                content = text[start:end].strip()
                content = _strip_code_fences(content)

                # Prevent path traversal — resolve and verify containment
                out_path = (output_dir / file_path).resolve()
                if not str(out_path).startswith(str(resolved_output)):
                    print(f"  Skipping unsafe path: {file_path}", file=sys.stderr)
                    continue

                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(content, encoding="utf-8")
                saved.append(str(out_path))
        else:
            # Single file output
            content = _strip_code_fences(text)

            if not extension:
                extension = _detect_extension(content)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = output_dir / f"{filename}_{timestamp}{extension}"
            out_path.write_text(content, encoding="utf-8")
            saved.append(str(out_path))

        return saved

    def test_connection(self) -> bool:
        """Test API connectivity with a minimal request."""
        try:
            response = self.generate(
                "Respond with exactly: OK",
                thinking="low",
            )
            text = self.extract_text(response)
            print(f"Connection OK. Response: {text[:100]}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}", file=sys.stderr)
            return False


def _strip_code_fences(text: str) -> str:
    """Remove wrapping markdown code fences from generated code."""
    text = text.strip()
    lines = text.split("\n")
    # Check if first line is a fence (```lang or ```) and last non-empty line is ```
    if len(lines) >= 2 and lines[0].startswith("```"):
        # Find last non-empty line
        end = len(lines) - 1
        while end > 0 and lines[end].strip() == "":
            end -= 1
        if lines[end].strip() == "```":
            return "\n".join(lines[1:end])
    return text


def _detect_extension(content: str) -> str:
    """Detect file extension from code content."""
    if re.search(r'\bimport\b.*\bfrom\b.*[\'"]react[\'"]', content):
        return ".tsx"
    if re.search(r'<svg\b', content, re.IGNORECASE):
        return ".svg"
    if re.search(r'<!DOCTYPE|<html', content, re.IGNORECASE):
        return ".html"
    if re.search(r'\bexport\b.*\bfunction\b|\bconst\b.*=.*=>|import\b.*from\b', content):
        return ".tsx"
    if re.search(r'@tailwind|@theme|@apply', content):
        return ".css"
    return ".html"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Forge Text Client")
    parser.add_argument("--test", action="store_true", help="Test API connection")
    parser.add_argument("--api-key", help="API key (overrides GEMINI_API_KEY)")
    args = parser.parse_args()

    if args.test:
        client = GeminiForgeClient(api_key=args.api_key)
        success = client.test_connection()
        sys.exit(0 if success else 1)
    else:
        print("Gemini Forge Text Client")
        print("========================")
        print()
        print("Library usage:")
        print("    from gemini_text import GeminiForgeClient")
        print("    client = GeminiForgeClient()")
        print('    response = client.generate("Build a React form")')
        print()
        print("Test connection:")
        print("    python gemini_text.py --test")
