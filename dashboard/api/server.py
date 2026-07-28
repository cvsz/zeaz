#!/usr/bin/env python3
"""Serve the engineering dashboard, JSON snapshot, and live SSE stream."""
from __future__ import annotations

import json
import os
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dashboard.api.health import snapshot

DASHBOARD = Path(__file__).resolve().parents[1]


def _positive_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


class DashboardHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD), **kwargs)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'")
        super().end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(snapshot())
        elif path == "/api/events":
            self._events()
        elif path in {"/", "/index.html"}:
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def _json(self, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _events(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        interval = _positive_int("DASHBOARD_REFRESH_SECONDS", 10, minimum=2)
        try:
            while True:
                body = json.dumps(snapshot(), ensure_ascii=False)
                self.wfile.write(f"event: health\ndata: {body}\n\n".encode())
                self.wfile.flush()
                time.sleep(interval)
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, message: str, *args: object) -> None:
        print(f"{self.address_string()} - {message % args}", flush=True)


def main() -> None:
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = _positive_int("DASHBOARD_PORT", 8080)
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Engineering dashboard listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
