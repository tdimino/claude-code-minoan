#!/usr/bin/env python3
"""
Nano Banana Pro Image Generation Library

A shared library for generating, editing, and composing images with Nano Banana Pro
(Gemini 3 Pro Image) API using the REST interface.

Usage:
    from gemini_images import NanoBananaProClient

    client = NanoBananaProClient(api_key="YOUR_KEY")

    # Generate image
    response = client.generate_image("A sunset over mountains")
    client.save_response("output.png", response)

    # Edit image
    response = client.edit_image("Add clouds", "input.png")
    client.save_response("edited.png", response)

    # Compose multiple images
    response = client.compose_images(
        "Create a collage of these scenes",
        ["img1.png", "img2.png", "img3.png"]
    )

Environment:
    GEMINI_API_KEY - API key for authentication
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

try:
    import requests
except ImportError:
    raise ImportError("requests library required. Run: pip install requests")


class NanoBananaProClient:
    """
    High-level client for Nano Banana Pro (Gemini 3 Pro Image) API.

    This client uses the REST API directly (not the Python SDK) for maximum
    control and compatibility with existing Nano Banana Pro scripts.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemini-3-pro-image-preview"
    FLASH_MODEL = "gemini-3.1-flash-image-preview"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Nano Banana Pro client.

        Args:
            api_key: API key (defaults to GEMINI_API_KEY env var)
            model: Model ID (defaults to MODEL / gemini-3-pro-image-preview)

        Raises:
            EnvironmentError: If no API key is provided
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("API key required. Set GEMINI_API_KEY or pass api_key parameter")

        self.model = model or self.MODEL
        self.endpoint = f"{self.BASE_URL}/{self.model}:generateContent"

    def _encode_image(self, image_path: Union[str, Path]) -> tuple:
        """
        Encode image file to base64.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, mime_type)
        """
        image_path = Path(image_path)

        # Determine MIME type
        ext_to_mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp"
        }
        mime_type = ext_to_mime.get(image_path.suffix.lower(), "image/png")

        # Read and encode
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return image_base64, mime_type

    def _make_request(
        self,
        parts: List[Dict[str, Any]],
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        timeout: int = 180
    ) -> Dict[str, Any]:
        """
        Make API request to Nano Banana Pro.

        Args:
            parts: Content parts (text and/or images)
            aspect_ratio: Output aspect ratio
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens
            timeout: Request timeout in seconds

        Returns:
            API response dictionary

        Raises:
            Exception: On API or network errors
        """
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
                "imageConfig": {
                    "aspectRatio": aspect_ratio
                }
            }
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = json.dumps(error_data, indent=2)
            except:
                error_detail = e.response.text

            raise Exception(f"API request failed: {e}\n{error_detail}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of image to generate
            aspect_ratio: Image aspect ratio (1:1, 3:4, 4:3, 9:16, 16:9)
            temperature: Creativity level (0.0-1.0)
            max_output_tokens: Maximum response tokens

        Returns:
            API response containing generated image

        Example:
            >>> client = NanoBananaProClient()
            >>> response = client.generate_image("A sunset over mountains")
            >>> client.save_response("sunset.png", response)
        """
        parts = [{"text": prompt}]
        return self._make_request(parts, aspect_ratio, temperature, max_output_tokens)

    def edit_image(
        self,
        instruction: str,
        image_path: Union[str, Path],
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Edit an existing image with natural language instructions.

        Args:
            instruction: Edit instruction (e.g., "Make the sky blue")
            image_path: Path to input image
            aspect_ratio: Output aspect ratio
            temperature: Creativity level (0.0-1.0)
            max_output_tokens: Maximum response tokens

        Returns:
            API response containing edited image

        Example:
            >>> client = NanoBananaProClient()
            >>> response = client.edit_image("Add clouds", "input.png")
            >>> client.save_response("edited.png", response)
        """
        # Encode image
        image_data, mime_type = self._encode_image(image_path)

        parts = [
            {"text": instruction},
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": image_data
                }
            }
        ]

        return self._make_request(parts, aspect_ratio, temperature, max_output_tokens)

    def compose_images(
        self,
        instruction: str,
        image_paths: List[Union[str, Path]],
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Compose multiple images into one based on instructions.

        Args:
            instruction: Composition instruction
            image_paths: List of input image paths (up to 14)
            aspect_ratio: Output aspect ratio
            temperature: Creativity level (0.0-1.0)
            max_output_tokens: Maximum response tokens

        Returns:
            API response containing composed image

        Raises:
            ValueError: If more than 14 images provided or less than 1

        Example:
            >>> client = NanoBananaProClient()
            >>> response = client.compose_images(
            ...     "Create a group photo",
            ...     ["person1.png", "person2.png", "person3.png"]
            ... )
            >>> client.save_response("group.png", response)
        """
        if len(image_paths) > 14:
            raise ValueError("Maximum 14 images supported")
        if len(image_paths) < 1:
            raise ValueError("At least 1 image required")

        # Build parts: instruction first, then all images
        parts = [{"text": instruction}]

        for image_path in image_paths:
            image_data, mime_type = self._encode_image(image_path)
            parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": image_data
                }
            })

        return self._make_request(parts, aspect_ratio, temperature, max_output_tokens)

    def save_response(
        self,
        output_path: Union[str, Path],
        response: Dict[str, Any],
        save_text: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Save image and optional text from API response.

        Args:
            output_path: Output file path for image
            response: API response dictionary
            save_text: Whether to save text responses

        Returns:
            Dictionary with 'image' and 'text' file paths (or None)

        Example:
            >>> response = client.generate_image("A sunset")
            >>> paths = client.save_response("sunset.png", response)
            >>> print(f"Image: {paths['image']}, Text: {paths['text']}")
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {"image": None, "text": None}

        try:
            candidates = response.get("candidates", [])
            if not candidates:
                raise Exception("No candidates in response")

            # Process first candidate
            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            for part in parts:
                # Save image
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    image_data = inline_data.get("data", "")

                    if not image_data:
                        continue

                    # Decode and save
                    image_bytes = base64.b64decode(image_data)
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)

                    result["image"] = str(output_path)

                # Save text response
                if "text" in part and save_text:
                    text_content = part["text"]
                    text_path = output_path.with_suffix(".txt")

                    with open(text_path, "w", encoding="utf-8") as f:
                        f.write(text_content)

                    result["text"] = str(text_path)

        except Exception as e:
            raise Exception(f"Failed to save response: {e}")

        return result


class ImageChat:
    """
    Multi-turn chat session for iterative image generation and refinement.

    Maintains conversation history and allows progressive image editing
    through natural conversation.
    """

    def __init__(self, client: NanoBananaProClient):
        """
        Initialize chat session.

        Args:
            client: NanoBananaProClient instance
        """
        self.client = client
        self.history: List[Dict[str, Any]] = []
        self.current_image: Optional[Path] = None

    def send(
        self,
        message: str,
        image_path: Optional[Union[str, Path]] = None,
        aspect_ratio: str = "16:9",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Send a message in the chat and optionally include an image.

        Args:
            message: Text message/instruction
            image_path: Optional image to include
            aspect_ratio: Output aspect ratio
            temperature: Creativity level

        Returns:
            API response

        Example:
            >>> chat = ImageChat(client)
            >>> response = chat.send("Create a logo for 'Acme Corp'")
            >>> response = chat.send("Make the text bolder")
            >>> response = chat.send("Add a blue gradient background")
        """
        # Use provided image or current image from history
        img_path = image_path or self.current_image

        if img_path:
            response = self.client.edit_image(
                instruction=message,
                image_path=img_path,
                aspect_ratio=aspect_ratio,
                temperature=temperature
            )
        else:
            response = self.client.generate_image(
                prompt=message,
                aspect_ratio=aspect_ratio,
                temperature=temperature
            )

        # Add to history
        self.history.append({
            "message": message,
            "image_path": str(img_path) if img_path else None,
            "response": response
        })

        return response

    def save_current(self, output_path: Union[str, Path]) -> Dict[str, Optional[str]]:
        """
        Save the most recent image from chat history.

        Args:
            output_path: Output file path

        Returns:
            Dictionary with saved file paths
        """
        if not self.history:
            raise Exception("No images in chat history")

        last_response = self.history[-1]["response"]
        paths = self.client.save_response(output_path, last_response)

        # Update current image reference
        if paths["image"]:
            self.current_image = Path(paths["image"])

        return paths

    def reset(self):
        """Reset the chat session, clearing history."""
        self.history = []
        self.current_image = None


# Convenience functions for quick usage

def generate(prompt: str, output: str, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
    """
    Quick generation function.

    Args:
        prompt: Text prompt
        output: Output file path
        api_key: Optional API key
        model: Optional model ID (default: gemini-3-pro-image-preview)
        **kwargs: Additional arguments (aspect_ratio, temperature, etc.)
    """
    client = NanoBananaProClient(api_key, model=model)
    response = client.generate_image(prompt, **kwargs)
    return client.save_response(output, response)


def edit(instruction: str, image: str, output: str, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
    """
    Quick editing function.

    Args:
        instruction: Edit instruction
        image: Input image path
        output: Output file path
        api_key: Optional API key
        model: Optional model ID (default: gemini-3-pro-image-preview)
        **kwargs: Additional arguments (aspect_ratio, temperature, etc.)
    """
    client = NanoBananaProClient(api_key, model=model)
    response = client.edit_image(instruction, image, **kwargs)
    return client.save_response(output, response)


def compose(instruction: str, images: List[str], output: str, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
    """
    Quick composition function.

    Args:
        instruction: Composition instruction
        images: List of input image paths
        output: Output file path
        api_key: Optional API key
        model: Optional model ID (default: gemini-3-pro-image-preview)
        **kwargs: Additional arguments (aspect_ratio, temperature, etc.)
    """
    client = NanoBananaProClient(api_key, model=model)
    response = client.compose_images(instruction, images, **kwargs)
    return client.save_response(output, response)


if __name__ == "__main__":
    print("Nano Banana Pro Image Generation Library")
    print("=========================================")
    print()
    print("This is a library module. Import it in your scripts:")
    print()
    print("    from gemini_images import NanoBananaProClient")
    print()
    print("    client = NanoBananaProClient()")
    print("    response = client.generate_image('A sunset over mountains')")
    print("    client.save_response('output.png', response)")
    print()
    print("For standalone generation, use generate_image.py instead.")
