"""GitPulse Web Server — zero-dependency, built on http.server."""

import json
import os
import mimetypes
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from .router import Router
from .templating import render

STATIC_DIR = Path(__file__).parent / "static"
DOCS_DIR = Path(__file__).parent.parent / "docs"

# Global mutable state
_gh = None
_config = {}
router = Router()


def get_gh():
    return _gh


def set_gh(gh):
    global _gh
    _gh = gh


def get_config():
    return _config


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Static files — always served
        if path.startswith("/static/"):
            self._serve_static(path[8:])
            return

        # Docs — always served
        if path.startswith("/docs/") or path == "/docs":
            doc_path = path[6:] or "index.html"
            if doc_path.startswith("/"):
                doc_path = doc_path[1:]
            if not doc_path or doc_path.endswith("/"):
                doc_path += "index.html"
            self._serve_doc(doc_path)
            return

        if path == "/favicon.ico":
            self._send(b"", 404)
            return

        # Welcome and tutorial — always accessible
        if path in ("/welcome", "/tutorial"):
            fn, kwargs = router.resolve("GET", path)
            if fn:
                result = fn(query=query, **kwargs)
                self._html(result)
            return

        # No gh yet → redirect to welcome (except API connect)
        if _gh is None and not path.startswith("/api/connect"):
            self._redirect("/welcome")
            return

        fn, kwargs = router.resolve("GET", path)
        if fn:
            try:
                result = fn(query=query, **kwargs)
                if isinstance(result, dict):
                    self._json(result)
                else:
                    self._html(result)
            except Exception as e:
                self._html(f"<h1>Error</h1><pre>{e}</pre>", 500)
        else:
            self._html(render("404.html"), 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        fn, kwargs = router.resolve("POST", path)
        if fn:
            try:
                result = fn(data=data, **kwargs)
                if isinstance(result, dict):
                    self._json(result)
                else:
                    self._html(result)
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "Not found"}, 404)

    def _html(self, content, code=200):
        body = content.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, code=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send(self, data, code=200, content_type="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location, code=302):
        self.send_response(code)
        self.send_header("Location", location)
        self.send_header("Content-Length", 0)
        self.end_headers()

    def _serve_static(self, filepath):
        full_path = STATIC_DIR / filepath
        if not full_path.exists() or not full_path.is_file():
            self._send(b"Not found", 404)
            return
        mime, _ = mimetypes.guess_type(str(full_path))
        data = full_path.read_bytes()
        self._send(data, 200, mime or "application/octet-stream")

    def _serve_doc(self, filepath):
        full_path = DOCS_DIR / filepath
        if not full_path.exists() or not full_path.is_file():
            self._send(b"Not found", 404)
            return
        mime, _ = mimetypes.guess_type(str(full_path))
        data = full_path.read_bytes()
        self._send(data, 200, mime or "text/html")

    def log_message(self, format, *args):
        pass


def start_server(gh, config):
    """Start the web server."""
    global _gh, _config
    _gh = gh
    _config = config

    # Import routes (registers them on the router)
    from . import routes as _

    host = config.get("web_host", "127.0.0.1")
    port = config.get("web_port", 5000)

    HTTPServer.allow_reuse_address = True
    try:
        server = HTTPServer((host, port), RequestHandler)
    except OSError:
        import subprocess, time
        subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(5):
            time.sleep(1)
            try:
                server = HTTPServer((host, port), RequestHandler)
                break
            except OSError:
                pass
        else:
            print(f"  Port {port} still busy. Try: lsof -ti:{port} | xargs kill -9")
            return
    url = f"http://{host}:{port}"

    from lib.colors import C
    print(f"  {C.BOLD}بسم الله الرحمن الرحيم{C.RESET}\n")
    print(f"  {C.GREEN}{C.BOLD}GitPulse Web UI{C.RESET}")
    print(f"  {C.CYAN}{url}{C.RESET}")
    if _gh is None:
        print(f"  {C.YELLOW}No token — welcome page will show{C.RESET}")
    print(f"  {C.DIM}Press Ctrl+C to stop{C.RESET}\n")

    if config.get("web_auto_open", True):
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n  {C.YELLOW}Server stopped.{C.RESET}")
        server.server_close()
