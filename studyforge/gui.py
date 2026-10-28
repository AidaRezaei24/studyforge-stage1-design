"""Loopback-only browser boundary. All business behavior stays in the controller."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import secrets

ASSETS = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}
MAX_BODY = 256 * 1024


def make_handler(controller, token=None):
    csrf = token or secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Request bodies and model failures are never written to server logs.
            pass

        def send(self, status, body, content_type="application/json; charset=utf-8"):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def trusted_host(self):
            return self.headers.get("Host", "") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.trusted_host():
                return self.send(403, {"error": "Use the printed 127.0.0.1 workspace URL."})
            if self.path == "/api/bootstrap":
                return self.send(200, {"token": csrf})
            asset = ASSETS.get(self.path)
            if not asset:
                return self.send(404, {"error": "Not found"})
            filename, content_type = asset
            self.send(200, (Path(__file__).parent / "web" / filename).read_bytes(), content_type)

        def do_POST(self):
            origin = self.headers.get("Origin")
            expected = f"http://127.0.0.1:{self.server.server_port}"
            if not self.trusted_host() or (origin and origin != expected) or self.headers.get("X-StudyForge-Token") != csrf:
                return self.send(403, {"error": "Untrusted workspace request. Reload the workspace."})
            if self.path != "/api/action":
                return self.send(404, {"error": "Not found"})
            if self.headers.get_content_type() != "application/json":
                return self.send(415, {"error": "JSON required"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > MAX_BODY:
                    return self.send(413, {"error": "Request must be between 1 byte and 256 KiB"})
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict) or not isinstance(payload.get("action"), str) or not isinstance(payload.get("params", {}), dict):
                    raise ValueError("Expected action and parameter object")
                result = controller.handle(payload["action"], **payload.get("params", {}))
                self.send(200, {"result": result})
            except (ValueError, KeyError, TypeError) as error:
                self.send(400, {"error": str(error)})
            except (OSError, RuntimeError) as error:
                self.send(422, {"error": str(error)})
            except Exception:
                self.send(500, {"error": "The operation failed. Please check your local configuration and try again."})

    return Handler


def serve(controller, port=8765):
    with HTTPServer(("127.0.0.1", port), make_handler(controller)) as server:
        print(f"StudyForge workspace: http://127.0.0.1:{server.server_port}", flush=True)
        print("Press Ctrl+C to stop. Your work is saved locally.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
