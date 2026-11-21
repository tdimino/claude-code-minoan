"""Tests for fetch_osha.py against a local stub server. Nothing leaves the machine."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch_osha  # noqa: E402


class Stub(BaseHTTPRequestHandler):
    """Answers every GET with the reply the test set, and records the request."""

    status = 200
    content_type = "application/json"
    body = b"{}"
    seen: list[dict] = []

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        type(self).seen.append({
            "path": parsed.path,
            "params": dict(urllib.parse.parse_qsl(parsed.query)),
        })
        self.send_response(type(self).status)
        self.send_header("Content-Type", type(self).content_type)
        self.end_headers()
        self.wfile.write(type(self).body)

    def log_message(self, *args):
        pass


class FetchOshaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Stub)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/v4/get/OSHA/inspection/json"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Stub.status, Stub.content_type, Stub.body, Stub.seen = 200, "application/json", b"{}", []
        patches = [
            mock.patch.object(fetch_osha, "DOL_BASE", self.base),
            mock.patch.dict(os.environ, {"DOL_API_KEY": "test-key"}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def reply(self, body, status=200, content_type="application/json"):
        Stub.status, Stub.content_type = status, content_type
        Stub.body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def test_html_reply_is_reported_as_a_moved_endpoint(self):
        # What the retired endpoint did: a redirect that ends on an HTML page with status 200.
        self.reply(b"<!doctype html><html><body>Open Data Portal</body></html>",
                   content_type="text/html")
        with self.assertRaisesRegex(RuntimeError, "not JSON"):
            fetch_osha.search_inspections(query="Acme")

    def test_request_carries_key_filters_and_sort(self):
        self.reply({"data": []})
        fetch_osha.search_inspections(query="Acme Mfg", state="TX", sic="2911", limit=7)
        params = Stub.seen[-1]["params"]
        self.assertEqual(Stub.seen[-1]["path"], "/v4/get/OSHA/inspection/json")
        self.assertEqual(params["X-API-KEY"], "test-key")
        self.assertEqual((params["limit"], params["sort"], params["sort_by"]),
                         ("7", "desc", "open_date"))
        self.assertEqual(json.loads(params["filter_object"]), {"and": [
            {"field": "estab_name", "operator": "like", "value": "%ACME MFG%"},
            {"field": "site_state", "operator": "eq", "value": "TX"},
            {"field": "sic_code", "operator": "eq", "value": "2911"},
        ]})

    def test_single_filter_is_sent_bare(self):
        self.reply({"data": []})
        fetch_osha.search_inspections(state="ny")
        self.assertEqual(json.loads(Stub.seen[-1]["params"]["filter_object"]),
                         {"field": "site_state", "operator": "eq", "value": "NY"})

    def test_records_are_read_from_data(self):
        self.reply({"data": [{"activity_nr": 123, "estab_name": "ACME", "total_current_penalty": 50}]})
        records = fetch_osha.search_inspections(query="acme")
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0]["activity_nr"], records[0]["estab_name"], records[0]["total_penalty"]),
                         ("123", "ACME", 50))

    def test_missing_key_stops_before_any_request(self):
        err = io.StringIO()
        with mock.patch.dict(os.environ, clear=True), contextlib.redirect_stderr(err), \
                self.assertRaises(SystemExit):
            fetch_osha.search_inspections(query="Acme")
        self.assertIn("DOL_API_KEY", err.getvalue())
        self.assertEqual(Stub.seen, [])

    def test_rejected_key_is_named(self):
        self.reply(b"The API key is either incorrect or missing from your query.",
                   status=401, content_type="text/plain")
        with self.assertRaisesRegex(RuntimeError, "rejected the API key"):
            fetch_osha.search_inspections(query="Acme")

    def test_errors_and_provenance_never_hold_the_key(self):
        self.reply(b"<html></html>", content_type="text/html")
        with self.assertRaises(RuntimeError) as caught:
            fetch_osha.search_inspections(query="Acme")
        self.assertNotIn("test-key", str(caught.exception))
        with tempfile.TemporaryDirectory() as tmp:
            fetch_osha.write_results(Path(tmp), [], {"query": "Acme", "state": None, "sic": None})
            written = (Path(tmp) / "datasets" / "scraped" / "osha" / "provenance.json").read_text()
        self.assertNotIn("test-key", written)


if __name__ == "__main__":
    unittest.main()
