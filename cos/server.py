"""Minimal HTTP server (stdlib only). Binds to localhost by default."""
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import ROOT

STATIC = ROOT / "static"


def make_handler(store, scheduler):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/api/status":
                return self._json(scheduler.status())
            if path == "/api/briefings":
                return self._json(store.list())
            if path == "/api/briefings/latest":
                b = store.latest()
                return self._json(b or {}, 200 if b else 404)
            if path.startswith("/api/briefings/"):
                b = store.get(path.rsplit("/", 1)[1])
                return self._json(b or {"error": "not found"}, 200 if b else 404)
            f = (STATIC / ("index.html" if path in ("/", "") else path.lstrip("/"))).resolve()
            if STATIC.resolve() not in f.parents or not f.is_file():
                return self._json({"error": "not found"}, 404)
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            # Reject cross-site POSTs (CSRF): browsers always send Origin on cross-origin POST.
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            if origin and origin.split("://", 1)[-1] != host:
                return self._json({"error": "forbidden"}, 403)
            if self.path == "/api/generate":
                started = scheduler.trigger_async()
                return self._json({"started": started, "running": scheduler.running}, 202 if started else 409)
            return self._json({"error": "not found"}, 404)

    return H


def serve(cfg, store, scheduler, host="127.0.0.1"):
    srv = ThreadingHTTPServer((host, cfg["port"]), make_handler(store, scheduler))
    print(f"Chief of Staff running at http://{host}:{cfg['port']}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        srv.server_close()
