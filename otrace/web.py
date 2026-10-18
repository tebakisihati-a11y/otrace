"""Otrace web dashboard — serve index.html + API."""

import json
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

OTRACE_DIR = Path(__file__).parent.parent
INDEX_HTML = OTRACE_DIR / "index.html"


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self._serve_index()
        elif path == "/api/status":
            self._api_status()
        elif path == "/api/tools":
            self._api_tools()
        elif path == "/api/runs":
            self._api_runs()
        elif path == "/api/health":
            self._api_health()
        else:
            super().do_GET()

    def _serve_index(self):
        html = INDEX_HTML.read_text()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _api_status(self):
        try:
            r = subprocess.run(
                ["python3", "-m", "otrace", "doctor"],
                capture_output=True, text=True, timeout=30,
                cwd=str(OTRACE_DIR),
            )
            self._json({"ok": True, "output": r.stdout, "rc": r.returncode})
        except Exception as e:
            self._json({"ok": False, "error": str(e)})

    def _api_tools(self):
        try:
            r = subprocess.run(
                ["python3", "-m", "otrace", "tools"],
                capture_output=True, text=True, timeout=10,
                cwd=str(OTRACE_DIR),
            )
            self._json({"ok": True, "output": r.stdout})
        except Exception as e:
            self._json({"ok": False, "error": str(e)})

    def _api_runs(self):
        runs_dir = OTRACE_DIR / ".otrace" / "runs"
        runs = []
        if runs_dir.exists():
            for d in sorted(runs_dir.iterdir(), reverse=True)[:20]:
                report = d / "report.json"
                if report.exists():
                    try:
                        data = json.loads(report.read_text())
                        runs.append({
                            "run_id": d.name,
                            "target": data.get("target", "?"),
                            "isolation_ok": data.get("isolation_ok", "?"),
                            "tools": [r.get("tool", "?") for r in data.get("results", [])],
                        })
                    except Exception:
                        pass
        self._json({"ok": True, "runs": runs})

    def _api_health(self):
        self._json({
            "ok": True,
            "service": subprocess.run(
                ["launchctl", "list"], capture_output=True, text=True
            ).stdout.count("otrace") > 0,
            "podman": "running" in subprocess.run(
                ["podman", "machine", "list"], capture_output=True, text=True
            ).stdout.lower(),
        })

    def _json(self, data):
        body = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # suppress default logging


def serve(port=8765):
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"[otrace] Web dashboard: http://127.0.0.1:{port}")
    print(f"[otrace] API: http://127.0.0.1:{port}/api/status")
    server.serve_forever()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    serve(port)
