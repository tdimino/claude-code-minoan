#!/usr/bin/env python3
"""Claude Code Session Picker - Visual interface for browsing and resuming sessions."""

import json
import subprocess
import os
import re
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import webbrowser
import threading

PORT = 4466

def get_sessions(limit=20):
    """Extract session data from Claude Code history."""
    history_file = Path.home() / ".claude" / "history.jsonl"
    projects_dir = Path.home() / ".claude" / "projects"

    # Build slug lookup from agent files
    slugs = {}
    if projects_dir.exists():
        for agent_file in projects_dir.rglob("agent-*.jsonl"):
            try:
                with open(agent_file) as f:
                    for line in f:
                        data = json.loads(line)
                        if data.get("slug") and data.get("sessionId"):
                            slugs[data["sessionId"]] = data["slug"]
            except:
                pass

    # Load history
    sessions = {}
    if history_file.exists():
        with open(history_file) as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    sid = msg.get("sessionId")
                    if not sid:
                        continue
                    if sid not in sessions:
                        sessions[sid] = {
                            "sessionId": sid,
                            "project": msg.get("project", ""),
                            "messages": [],
                            "timestamp": msg.get("timestamp", 0)
                        }
                    sessions[sid]["messages"].append({
                        "display": msg.get("display", ""),
                        "timestamp": msg.get("timestamp", 0)
                    })
                    sessions[sid]["timestamp"] = max(sessions[sid]["timestamp"], msg.get("timestamp", 0))
                except:
                    pass

    # Process sessions
    result = []
    for sid, data in sessions.items():
        msgs = sorted(data["messages"], key=lambda x: x["timestamp"])
        all_text = " ".join(m["display"] for m in msgs).lower()

        # Categorize
        tags = []
        if re.search(r"bug|error|broken|issue|debug|crash", all_text):
            tags.append({"emoji": "🐛", "name": "bug"})
        if re.search(r"add|create|implement|build|new feature", all_text):
            tags.append({"emoji": "✨", "name": "feature"})
        if re.search(r"investigate|explore|search|research|understand", all_text):
            tags.append({"emoji": "🔍", "name": "research"})
        if re.search(r"refactor|rename|clean|reorganize|simplify", all_text):
            tags.append({"emoji": "♻️", "name": "refactor"})
        if re.search(r"style|css|design|ui|layout|tailwind", all_text):
            tags.append({"emoji": "🎨", "name": "design"})
        if re.search(r"test|spec|jest|pytest|coverage", all_text):
            tags.append({"emoji": "🧪", "name": "test"})
        if re.search(r"deploy|docker|ci|cd|pipeline|release", all_text):
            tags.append({"emoji": "🚀", "name": "deploy"})
        tags = tags[:3]

        # Extract keywords - only markdown files in plan/plans folders
        all_text = " ".join(m["display"] for m in msgs)
        # Match patterns like plans/foo.md or plan/bar.md
        raw_keywords = list(set(re.findall(r"plans?/([A-Za-z][A-Za-z0-9_-]{1,30})\.md", all_text)))
        keywords = raw_keywords[:4]

        # Topic
        topic_msgs = [m for m in msgs[1:] if len(m["display"]) > 15]
        topic = topic_msgs[0]["display"][:60] if topic_msgs else ""

        result.append({
            "sessionId": sid,
            "project": data["project"],
            "projectName": Path(data["project"]).name if data["project"] else "",
            "messages": len(msgs),
            "timestamp": data["timestamp"],
            "slug": slugs.get(sid, ""),
            "tags": tags,
            "keywords": keywords,
            "topic": topic.replace("\n", " "),
            "latest": msgs[-1]["display"][:50].replace("\n", " ") if msgs else ""
        })

    result.sort(key=lambda x: x["timestamp"], reverse=True)
    return result[:limit]

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Claude Code Sessions</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e0e0e0;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
            color: #fff;
            font-size: 24px;
        }
        .sessions {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .session {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .session:hover {
            background: rgba(255,255,255,0.1);
            transform: translateX(4px);
            border-color: #818cf8;
        }
        .session-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }
        .session-num {
            background: #818cf8;
            color: #fff;
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }
        .session-tags { font-size: 18px; }
        .session-slug {
            color: #c084fc;
            font-weight: 600;
            flex-grow: 1;
        }
        .session-time {
            color: #4ade80;
            font-size: 13px;
        }
        .session-labels {
            color: #888;
            font-size: 12px;
            margin-left: 38px;
            margin-bottom: 6px;
        }
        .session-keywords {
            color: #fbbf24;
            font-size: 12px;
            margin-left: 38px;
            margin-bottom: 6px;
        }
        .session-project {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: 38px;
            font-size: 13px;
        }
        .project-name { color: #22d3d1; font-weight: 500; }
        .msg-count { color: #888; }
        .session-topic {
            margin-left: 38px;
            margin-top: 8px;
            color: #60a5fa;
            font-size: 13px;
        }
        .session-id {
            margin-left: 38px;
            color: #666;
            font-size: 11px;
            margin-top: 4px;
        }
        .btn-resume {
            background: #4ade80;
            color: #000;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 12px;
        }
        .btn-resume:hover { background: #22c55e; }
        .legend {
            max-width: 900px;
            margin: 20px auto 0;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>Claude Code Sessions</h1>
    <div class="sessions" id="sessions"></div>
    <div class="legend">
        🐛 bug · ✨ feature · 🔍 research · ♻️ refactor · 🎨 design · 🧪 test · 🚀 deploy
    </div>
    <script>
        const sessions = SESSION_DATA;

        function formatTime(ts) {
            const d = new Date(ts);
            return d.toLocaleDateString('en-US', {month: 'short', day: 'numeric'}) + ' ' +
                   d.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'});
        }

        function resumeSession(sid, project) {
            fetch('/resume?sid=' + sid + '&project=' + encodeURIComponent(project))
                .then(() => {
                    document.body.innerHTML = '<h1 style="text-align:center;margin-top:100px;color:#4ade80;">Opening VSCode...</h1><p style="text-align:center;color:#888;">Resume command copied to clipboard</p>';
                    setTimeout(() => window.close(), 2000);
                });
        }

        const container = document.getElementById('sessions');
        sessions.forEach((s, i) => {
            const tags = s.tags.map(t => t.emoji).join('');
            const labels = s.tags.map(t => t.name).join(', ');
            const keywords = s.keywords.length ? '📄 ' + s.keywords.join(', ') : '';

            container.innerHTML += `
                <div class="session" onclick="resumeSession('${s.sessionId}', '${s.project.replace(/'/g, "\\'")}')">
                    <div class="session-header">
                        <span class="session-num">${i + 1}</span>
                        <span class="session-tags">${tags}</span>
                        <span class="session-slug">${s.slug || '(unnamed)'}</span>
                        <span class="session-time">${formatTime(s.timestamp)}</span>
                    </div>
                    ${labels ? `<div class="session-labels">(${labels})</div>` : ''}
                    ${keywords ? `<div class="session-keywords">${keywords}</div>` : ''}
                    <div class="session-project">
                        <span class="project-name">${s.projectName}</span>
                        <span class="msg-count">${s.messages} msgs</span>
                    </div>
                    ${s.topic ? `<div class="session-topic">📌 ${s.topic}</div>` : ''}
                    <div class="session-id">ID: ${s.sessionId.slice(0, 8)}...</div>
                </div>
            `;
        });
    </script>
</body>
</html>
"""

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/resume":
            params = parse_qs(parsed.query)
            sid = params.get("sid", [""])[0]
            project = params.get("project", [""])[0]

            if sid and project and os.path.isdir(project):
                # Open VSCode
                subprocess.run(["code", project])
                # Copy resume command to clipboard
                subprocess.run(["pbcopy"], input=f"claude --resume {sid}".encode())

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        # Serve main page
        sessions = get_sessions(20)
        html = HTML_TEMPLATE.replace("SESSION_DATA", json.dumps(sessions))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass  # Suppress logs

def main():
    # Kill any existing server on this port
    subprocess.run(f"lsof -ti:{PORT} | xargs kill -9 2>/dev/null", shell=True)

    server = HTTPServer(("", PORT), Handler)
    print(f"Session picker running at http://localhost:{PORT}")

    # Open browser
    threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()
