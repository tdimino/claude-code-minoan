import sys
import tempfile
import unittest
from pathlib import Path

import requests

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts.atlas_images import AtlasImageClient, DEFAULT_ATLAS_MODEL


class FakeResponse:
    def __init__(self, payload=None, content=b"", content_type="application/json", status=200):
        self._payload = payload
        self.content = content
        self.headers = {"Content-Type": content_type}
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error


class AtlasImageClientTests(unittest.TestCase):
    def test_generation_posts_once_and_saves_completed_output(self):
        calls = []

        def request(method, url, **kwargs):
            calls.append((method, url, kwargs))
            if url.endswith("/api/v1/models"):
                return FakeResponse({"data": [{"model": DEFAULT_ATLAS_MODEL, "display_console": True}]})
            if url.endswith("/api/v1/model/generateImage"):
                return FakeResponse({"data": {"id": "prediction-1"}})
            if url.endswith("/api/v1/model/prediction/prediction-1"):
                return FakeResponse({"data": {"status": "completed", "outputs": ["https://cdn.example/image"]}})
            return FakeResponse(content=b"png-bytes", content_type="image/png")

        client = AtlasImageClient(api_key="test-key", request=request, sleep=lambda _: None)
        with tempfile.TemporaryDirectory() as tmp:
            output = client.generate_to_file(
                "bronze age harbor at sunrise",
                Path(tmp) / "generated",
                aspect_ratio="16:9",
                resolution="2k",
                temperature=0.8,
            )
            self.assertEqual(output.suffix, ".png")
            self.assertEqual(output.read_bytes(), b"png-bytes")

        post_calls = [call for call in calls if call[0] == "POST"]
        self.assertEqual(len(post_calls), 1)
        self.assertEqual(
            post_calls[0][2]["json"],
            {
                "model": DEFAULT_ATLAS_MODEL,
                "prompt": "bronze age harbor at sunrise",
                "aspect_ratio": "16:9",
                "resolution": "2k",
                "temperature": 0.8,
            },
        )

    def test_prediction_get_has_bounded_transient_retries(self):
        attempts = 0

        def request(method, url, **kwargs):
            nonlocal attempts
            attempts += 1
            raise requests.ConnectionError("offline")

        client = AtlasImageClient(api_key="test-key", request=request, sleep=lambda _: None)
        with self.assertRaises(requests.ConnectionError):
            client._poll_prediction("prediction-2")
        self.assertEqual(attempts, 4)

    def test_hidden_model_is_rejected_before_generation(self):
        def request(method, url, **kwargs):
            return FakeResponse({"data": [{"model": DEFAULT_ATLAS_MODEL, "display_console": False}]})

        client = AtlasImageClient(api_key="test-key", request=request)
        with self.assertRaisesRegex(RuntimeError, "not enabled"):
            client.validate_model()


if __name__ == "__main__":
    unittest.main()
