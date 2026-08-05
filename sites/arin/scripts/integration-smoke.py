#!/usr/bin/env python3
"""Exercise the Arin backend through a temporary loopback process."""

from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cryptography.fernet import Fernet


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def request(port: int, method: str, path: str, payload=None, cookie="", csrf=""):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    if cookie:
        headers["Cookie"] = cookie
    if csrf:
        headers["X-CSRF-Token"] = csrf
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    response_headers = dict(response.getheaders())
    connection.close()
    if "application/json" in response_headers.get("Content-Type", "") and raw:
        parsed = json.loads(raw.decode("utf-8"))
    else:
        parsed = raw
    return response.status, response_headers, parsed


def assert_status(actual: int, expected: int, path: str) -> None:
    if actual != expected:
        raise AssertionError(f"{path}: expected {expected}, got {actual}")


def main() -> None:
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="arin-smoke-") as temp_dir:
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": str(ROOT),
                "ARIN_DATA_DIR": str(Path(temp_dir) / "data"),
                "ARIN_CONNECTOR_KEY": Fernet.generate_key().decode("ascii"),
                "ARIN_PORT": str(port),
                "ARIN_HOST": "127.0.0.1",
            }
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "arin_app.server"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                try:
                    status, _, _ = request(port, "GET", "/api/health")
                    if status == 200:
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
                raise AssertionError(f"backend did not become healthy: {stderr}")

            status, _, _ = request(
                port,
                "POST",
                "/api/auth/register",
                {"email": "smoke@example.com", "name": "Smoke User", "password": "a sufficiently long password"},
            )
            assert_status(status, 201, "/api/auth/register")
            status, headers, login = request(
                port,
                "POST",
                "/api/auth/login",
                {"email": "smoke@example.com", "password": "a sufficiently long password"},
            )
            assert_status(status, 200, "/api/auth/login")
            cookie = headers["Set-Cookie"].split(";", 1)[0]
            status, _, session = request(port, "GET", "/api/auth/session", cookie=cookie)
            assert_status(status, 200, "/api/auth/session")
            csrf = session["csrf_token"]
            if "session_token" in login:
                raise AssertionError("login leaked a session token")

            status, _, workspace_body = request(
                port, "POST", "/api/workspaces", {"name": "Smoke Workspace"}, cookie, csrf
            )
            assert_status(status, 201, "/api/workspaces")
            workspace_id = workspace_body["workspace"]["id"]
            status, _, project_body = request(
                port,
                "POST",
                "/api/projects",
                {"workspace_id": workspace_id, "prompt": "Build a smoke test CRM", "category": "internal"},
                cookie,
                csrf,
            )
            assert_status(status, 201, "/api/projects")
            project_id = project_body["project"]["id"]
            status, _, _ = request(
                port,
                "PUT",
                f"/api/projects/{project_id}/files/index.html",
                {"content": "<!doctype html><title>Smoke published app</title>"},
                cookie,
                csrf,
            )
            assert_status(status, 200, "file edit")
            status, preview_headers, preview = request(port, "GET", f"/preview/{project_id}", cookie=cookie)
            assert_status(status, 200, "preview")
            if b"Smoke published app" not in preview or "sandbox" not in preview_headers.get("Content-Security-Policy", ""):
                raise AssertionError("preview did not return the isolated edited app")
            status, _, deployment_body = request(
                port, "POST", f"/api/projects/{project_id}/publish", {}, cookie, csrf
            )
            assert_status(status, 200, "publish")
            slug = deployment_body["deployment"]["slug"]
            status, _, public_app = request(port, "GET", f"/app/{slug}")
            assert_status(status, 200, "public app")
            if b"Smoke published app" not in public_app:
                raise AssertionError("published app did not contain the edited version")
            status, _, _ = request(
                port, "POST", f"/api/projects/{project_id}/unpublish", {}, cookie, csrf
            )
            assert_status(status, 204, "unpublish")
            status, _, _ = request(port, "GET", f"/app/{slug}")
            assert_status(status, 404, "unpublished app")
            print("Arin integration smoke passed: auth, project build, edit, preview, publish, and unpublish.")
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


if __name__ == "__main__":
    main()
