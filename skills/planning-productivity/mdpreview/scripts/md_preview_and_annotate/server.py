"""HTTP server — serves the HTML shell and API endpoints."""

import datetime
import http.server
import json
import os
import uuid
from urllib.parse import urlparse, parse_qs

from . import annotations
from .template import get_html


class PreviewHandler(http.server.BaseHTTPRequestHandler):
    _tabs = {}
    default_author = "Tom"

    def log_message(self, format, *args):
        pass

    @classmethod
    def add_tab(cls, filepath):
        tab_id = uuid.uuid4().hex[:8]
        try:
            with open(filepath) as f:
                content = f.read()
            mtime = os.path.getmtime(filepath)
        except Exception:
            content = ""
            mtime = 0
        cls._tabs[tab_id] = {
            "filepath": filepath,
            "content": content,
            "mtime": mtime,
        }
        return tab_id

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/api/content":
            tab_id = params.get("tab", [None])[0]
            if tab_id and tab_id in self._tabs:
                tab = self._tabs[tab_id]
                try:
                    mtime = os.path.getmtime(tab["filepath"])
                    if mtime != tab["mtime"]:
                        with open(tab["filepath"]) as f:
                            tab["content"] = f.read()
                        tab["mtime"] = mtime
                except Exception:
                    pass
                self._json_response({
                    "content": tab["content"],
                    "mtime": tab["mtime"],
                })
            else:
                self._json_response({"error": "tab not found"}, 404)

        elif parsed.path == "/api/tabs":
            tabs_list = []
            for tid in self._tabs:
                tabs_list.append({
                    "id": tid,
                    "filename": os.path.basename(self._tabs[tid]["filepath"]),
                    "filepath": self._tabs[tid]["filepath"],
                })
            self._json_response(tabs_list)

        elif parsed.path == "/api/annotations":
            tab_id = params.get("tab", [None])[0]
            if tab_id and tab_id in self._tabs:
                filepath = self._tabs[tab_id]["filepath"]
                data, mtime = annotations.read(filepath)
                self._json_response({
                    "annotations": data.get("annotations", []),
                    "mtime": mtime,
                })
            else:
                self._json_response({"error": "tab not found"}, 404)

        else:
            # Serve HTML shell
            first_tab = next(iter(self._tabs), "")
            first_file = self._tabs[first_tab]["filepath"] if first_tab else ""
            title = os.path.basename(first_file) if first_file else "mdpreview"
            html = get_html(title=title, default_author=self.default_author)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

    def do_POST(self):
        parsed = urlparse(self.path)
        body = self._read_body()

        if parsed.path == "/api/add":
            filepath = body.get("filepath", "")
            if not filepath:
                self._json_response({"error": "filepath required"}, 400)
                return
            if not os.path.isabs(filepath):
                first_tab = next(iter(self._tabs.values()), None)
                if first_tab:
                    base_dir = os.path.dirname(first_tab["filepath"])
                    filepath = os.path.join(base_dir, filepath)
            filepath = os.path.abspath(filepath)

            if not os.path.isfile(filepath):
                self._json_response({"error": f"file not found: {filepath}"}, 400)
                return

            # Check if already open
            for tid, tab in self._tabs.items():
                if tab["filepath"] == filepath:
                    self._json_response({
                        "id": tid,
                        "filename": os.path.basename(filepath),
                        "filepath": filepath,
                        "existing": True,
                    })
                    return

            tab_id = self.add_tab(filepath)
            self._json_response({
                "id": tab_id,
                "filename": os.path.basename(filepath),
                "filepath": filepath,
            })

        elif parsed.path == "/api/close":
            tab_id = body.get("id", "")
            if tab_id in self._tabs:
                del self._tabs[tab_id]
                self._json_response({"ok": True})
            else:
                self._json_response({"error": "tab not found"}, 404)

        elif parsed.path == "/api/annotate":
            tab_id = body.get("tab", "")
            if tab_id not in self._tabs:
                self._json_response({"error": "tab not found"}, 404)
                return
            filepath = self._tabs[tab_id]["filepath"]
            data, _ = annotations.read(filepath)

            ann = {
                "id": uuid.uuid4().hex[:6],
                "anchor": body.get("anchor", {}),
                "author": body.get("author", {}),
                "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "body": body.get("body", ""),
                "resolved": False,
                "replies": [],
            }
            data["annotations"].append(ann)
            annotations.write(filepath, data)
            self._json_response({"ok": True, "id": ann["id"]})

        elif parsed.path == "/api/resolve":
            tab_id = body.get("tab", "")
            ann_id = body.get("id", "")
            if tab_id not in self._tabs:
                self._json_response({"error": "tab not found"}, 404)
                return
            filepath = self._tabs[tab_id]["filepath"]
            data, _ = annotations.read(filepath)
            for ann in data["annotations"]:
                if ann["id"] == ann_id:
                    ann["resolved"] = not ann.get("resolved", False)
                    break
            annotations.write(filepath, data)
            self._json_response({"ok": True})

        elif parsed.path == "/api/delete-annotation":
            tab_id = body.get("tab", "")
            ann_id = body.get("id", "")
            if tab_id not in self._tabs:
                self._json_response({"error": "tab not found"}, 404)
                return
            filepath = self._tabs[tab_id]["filepath"]
            data, _ = annotations.read(filepath)
            data["annotations"] = [a for a in data["annotations"] if a["id"] != ann_id]
            annotations.write(filepath, data)
            self._json_response({"ok": True})

        else:
            self.send_error(404)


def start(port, handler_class=PreviewHandler):
    """Create and return an HTTPServer bound to localhost:port."""
    return http.server.HTTPServer(("127.0.0.1", port), handler_class)
