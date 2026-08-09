"""Loopback HTTP API for the Arin application."""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from . import db, security
from .generator import OpenAICompatibleGenerator
from .service import (
    ArinService,
    AuthenticationError,
    AuthorizationError,
    CSRFError,
    NotFoundError,
    ConflictError,
    ServiceError,
    SessionError,
    SESSION_DAYS,
    PREVIEW_CSP,
    ValidationError,
)


MAX_JSON_BYTES = 256 * 1024
MAX_UPLOAD_JSON_BYTES = 7 * 1024 * 1024
SESSION_COOKIE = "arin_session"
WORKSPACE_ROUTE = re.compile(r"^/api/workspaces/([^/]+)$")
WORKSPACE_MEMBERS_ROUTE = re.compile(r"^/api/workspaces/([^/]+)/members$")
WORKSPACE_INVITES_ROUTE = re.compile(r"^/api/workspaces/([^/]+)/invites$")
PROJECT_ROUTE = re.compile(r"^/api/projects/([^/]+)$")
PROJECT_SETTINGS_ROUTE = re.compile(r"^/api/projects/([^/]+)/settings$")
PROJECT_VERSIONS_ROUTE = re.compile(r"^/api/projects/([^/]+)/versions$")
PROJECT_RESTORE_ROUTE = re.compile(r"^/api/projects/([^/]+)/versions/([^/]+)/restore$")
PROJECT_ASSETS_ROUTE = re.compile(r"^/api/projects/([^/]+)/assets$")
PROJECT_CONNECTORS_ROUTE = re.compile(r"^/api/projects/([^/]+)/connectors$")
PROJECT_MESSAGES_ROUTE = re.compile(r"^/api/projects/([^/]+)/messages$")
PROJECT_AUDIT_ROUTE = re.compile(r"^/api/projects/([^/]+)/audit$")
PROJECT_BUILD_ROUTE = re.compile(r"^/api/projects/([^/]+)/build$")
PROJECT_FILE_ROUTE = re.compile(r"^/api/projects/([^/]+)/files/(.+)$")
PROJECT_PREVIEW_ROUTE = re.compile(r"^/preview/([^/]+)$")
PROJECT_PUBLISH_ROUTE = re.compile(r"^/api/projects/([^/]+)/publish$")
PROJECT_UNPUBLISH_ROUTE = re.compile(r"^/api/projects/([^/]+)/unpublish$")
PUBLIC_APP_ROUTE = re.compile(r"^/app/([A-Za-z0-9_-]+)$")
PRIVATE_ASSET_ROUTE = re.compile(r"^/api/assets/([^/]+)$")
PUBLIC_ASSET_ROUTE = re.compile(r"^/api/public-assets/([^/]+)$")
CONNECTOR_ROUTE = re.compile(r"^/api/connectors/([^/]+)$")


class ArinHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, service: ArinService):
        super().__init__(server_address, ArinRequestHandler)
        self.service = service


class ArinRequestHandler(BaseHTTPRequestHandler):
    server: ArinHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        # Keep access logs free of request bodies, cookies, and authorization
        # material. The reverse proxy already records the request status.
        super().log_message(format, *args)

    def do_GET(self) -> None:
        with self.server.service.request_lock:
            return self._do_get()

    def _do_get(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        try:
            if path == "/api/health":
                return self.json_response(HTTPStatus.OK, {"status": "ok", "service": "arin"})
            if path == "/api/auth/session":
                session = self.server.service.session_from_cookie(self.cookies().get(SESSION_COOKIE, ""))
                return self.json_response(HTTPStatus.OK, session)
            if path == "/api/workspaces":
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK, {"workspaces": self.server.service.list_workspaces(user["id"])}
                )
            if path == "/api/projects":
                user = self.require_session(mutation=False)
                workspace_id = parse_qs(parsed_url.query).get("workspace_id", [None])[0]
                return self.json_response(
                    HTTPStatus.OK,
                    {"projects": self.server.service.list_projects(user["id"], workspace_id)},
                )
            match = WORKSPACE_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"workspace": self.server.service.workspace_payload(user["id"], match.group(1))},
                )
            match = WORKSPACE_MEMBERS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"members": self.server.service.list_workspace_members(user["id"], match.group(1))},
                )
            match = WORKSPACE_INVITES_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"invites": self.server.service.list_invites(user["id"], match.group(1))},
                )
            match = PROJECT_ASSETS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"assets": self.server.service.list_assets(user["id"], match.group(1))},
                )
            match = PROJECT_CONNECTORS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"connectors": self.server.service.list_connectors(user["id"], match.group(1))},
                )
            match = PROJECT_MESSAGES_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"messages": self.server.service.list_agent_messages(user["id"], match.group(1))},
                )
            match = PROJECT_AUDIT_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"events": self.server.service.list_audit_events(user["id"], match.group(1))},
                )
            match = PRIVATE_ASSET_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.raw_response(
                    *self.server.service.read_asset(match.group(1), user_id=user["id"])
                )
            match = PUBLIC_ASSET_ROUTE.fullmatch(path)
            if match:
                return self.raw_response(*self.server.service.read_asset(match.group(1), public=True))
            match = PROJECT_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                project = self.server.service.project_payload(match.group(1))
                self.server.service.require_membership(user["id"], project["workspace_id"], {"owner", "editor", "viewer"})
                return self.json_response(HTTPStatus.OK, {"project": project})
            match = PROJECT_VERSIONS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                return self.json_response(
                    HTTPStatus.OK,
                    {"versions": self.server.service.list_versions(user["id"], match.group(1))},
                )
            match = PROJECT_PREVIEW_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=False)
                project = self.server.service.project_payload(match.group(1))
                self.server.service.require_membership(user["id"], project["workspace_id"], {"owner", "editor", "viewer"})
                return self.raw_response(*self.server.service.read_preview(match.group(1)))
            match = PUBLIC_APP_ROUTE.fullmatch(path)
            if match:
                return self.raw_response(*self.server.service.read_published(match.group(1)))
            return self.error_response(HTTPStatus.NOT_FOUND, "not_found", "route was not found")
        except ServiceError as exc:
            return self.handle_service_error(exc)
        except Exception:
            return self.error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "request failed")

    def do_POST(self) -> None:
        with self.server.service.request_lock:
            return self._do_post()

    def _do_post(self) -> None:
        path = urlparse(self.path).path
        try:
            upload_request = PROJECT_ASSETS_ROUTE.fullmatch(path) is not None
            payload = {} if path == "/api/auth/logout" else self.read_json(
                MAX_UPLOAD_JSON_BYTES if upload_request else MAX_JSON_BYTES
            )
            if path == "/api/auth/register":
                user = self.server.service.register_user(
                    payload.get("email", ""), payload.get("name", ""), payload.get("password", "")
                )
                return self.json_response(HTTPStatus.CREATED, {"user": user})
            if path == "/api/auth/login":
                session_token = security.new_token()
                session = self.server.service.login_user(
                    payload.get("email", ""),
                    payload.get("password", ""),
                    session_token=session_token,
                )
                public_session = {key: value for key, value in session.items() if key != "session_token"}
                return self.json_response(
                    HTTPStatus.OK,
                    public_session,
                    set_cookie=self.session_cookie(session_token, self.server.service.session_days),
                )
            if path == "/api/auth/logout":
                user = self.require_session(mutation=True)
                del user
                self.server.service.logout(self.cookies().get(SESSION_COOKIE, ""))
                return self.empty_response(
                    HTTPStatus.NO_CONTENT, set_cookie=self.expired_session_cookie()
                )
            if path == "/api/workspaces":
                user = self.require_session(mutation=True)
                workspace = self.server.service.create_workspace(user["id"], payload.get("name", ""))
                return self.json_response(HTTPStatus.CREATED, {"workspace": workspace})
            match = WORKSPACE_INVITES_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                invite = self.server.service.invite_member(
                    user["id"],
                    match.group(1),
                    payload.get("email", ""),
                    payload.get("role", "viewer"),
                    payload.get("ttl_days", 7),
                )
                return self.json_response(HTTPStatus.CREATED, {"invite": invite})
            match = WORKSPACE_MEMBERS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                member = self.server.service.add_workspace_member(
                    user["id"],
                    match.group(1),
                    payload.get("user_id", ""),
                    payload.get("role", "viewer"),
                )
                return self.json_response(HTTPStatus.CREATED, {"member": member})
            if path == "/api/invites/accept":
                user = self.require_session(mutation=True)
                membership = self.server.service.accept_invite(payload.get("token", ""), user["id"])
                return self.json_response(HTTPStatus.OK, {"membership": membership})
            if path == "/api/projects":
                user = self.require_session(mutation=True)
                project = self.server.service.create_project(
                    user["id"],
                    payload.get("workspace_id", ""),
                    payload.get("prompt", ""),
                    payload.get("category", "internal"),
                )
                return self.json_response(HTTPStatus.CREATED, {"project": project})
            match = PROJECT_ASSETS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                try:
                    asset_bytes = base64.b64decode(payload.get("data_base64", ""), validate=True)
                except (binascii.Error, TypeError, ValueError) as exc:
                    raise ValueError("asset data is not valid base64") from exc
                asset = self.server.service.add_asset(
                    user["id"],
                    match.group(1),
                    payload.get("filename", ""),
                    payload.get("mime_type", ""),
                    asset_bytes,
                )
                return self.json_response(HTTPStatus.CREATED, {"asset": asset})
            match = PROJECT_CONNECTORS_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                connector = self.server.service.create_connector(
                    user["id"],
                    match.group(1),
                    payload.get("kind", ""),
                    payload.get("label", ""),
                    payload.get("config", {}),
                )
                return self.json_response(HTTPStatus.CREATED, {"connector": connector})
            match = PROJECT_MESSAGES_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                message = self.server.service.append_agent_message(
                    user["id"],
                    match.group(1),
                    payload.get("role", "user"),
                    payload.get("content", ""),
                    payload.get("version_id"),
                )
                return self.json_response(HTTPStatus.CREATED, {"message": message})
            match = PROJECT_BUILD_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                project = self.server.service.build_project(
                    user["id"], match.group(1), payload.get("prompt", "")
                )
                return self.json_response(HTTPStatus.OK, {"project": project})
            match = PROJECT_RESTORE_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                version = self.server.service.restore_version(user["id"], match.group(1), match.group(2))
                return self.json_response(HTTPStatus.OK, {"version": version})
            match = PROJECT_PUBLISH_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                deployment = self.server.service.publish_project(user["id"], match.group(1))
                return self.json_response(HTTPStatus.OK, {"deployment": deployment})
            match = PROJECT_UNPUBLISH_ROUTE.fullmatch(path)
            if match:
                user = self.require_session(mutation=True)
                self.server.service.unpublish_project(user["id"], match.group(1))
                return self.empty_response(HTTPStatus.NO_CONTENT)
            return self.error_response(HTTPStatus.NOT_FOUND, "not_found", "route was not found")
        except ValueError as exc:
            return self.error_response(HTTPStatus.BAD_REQUEST, "invalid_json", str(exc))
        except ServiceError as exc:
            return self.handle_service_error(exc)
        except Exception:
            return self.error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "request failed")

    def do_PUT(self) -> None:
        with self.server.service.request_lock:
            return self._do_put()

    def _do_put(self) -> None:
        path = urlparse(self.path).path
        try:
            match = PROJECT_SETTINGS_ROUTE.fullmatch(path)
            if match:
                payload = self.read_json()
                user = self.require_session(mutation=True)
                settings = self.server.service.update_project_settings(
                    user["id"], match.group(1), payload.get("settings", payload)
                )
                return self.json_response(HTTPStatus.OK, {"settings": settings})
            match = CONNECTOR_ROUTE.fullmatch(path)
            if match:
                payload = self.read_json()
                user = self.require_session(mutation=True)
                connector = self.server.service.set_connector_status(
                    user["id"], match.group(1), payload.get("status", "")
                )
                return self.json_response(HTTPStatus.OK, {"connector": connector})
            match = PROJECT_FILE_ROUTE.fullmatch(path)
            if not match:
                return self.error_response(HTTPStatus.NOT_FOUND, "not_found", "route was not found")
            payload = self.read_json()
            user = self.require_session(mutation=True)
            version = self.server.service.update_file(
                user["id"], match.group(1), unquote(match.group(2)), payload.get("content", "")
            )
            return self.json_response(HTTPStatus.OK, {"version": version})
        except ValueError as exc:
            return self.error_response(HTTPStatus.BAD_REQUEST, "invalid_json", str(exc))
        except ServiceError as exc:
            return self.handle_service_error(exc)
        except Exception:
            return self.error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "request failed")

    def cookies(self) -> dict[str, str]:
        parsed = SimpleCookie()
        parsed.load(self.headers.get("Cookie", ""))
        return {key: morsel.value for key, morsel in parsed.items()}

    def require_session(self, mutation: bool) -> dict[str, Any]:
        session_token = self.cookies().get(SESSION_COOKIE, "")
        if mutation:
            return self.server.service.authenticate_session(
                session_token, self.headers.get("X-CSRF-Token", "")
            )
        return self.server.service.session_user(session_token)

    def read_json(self, max_bytes: int = MAX_JSON_BYTES) -> dict[str, Any]:
        length_value = self.headers.get("Content-Length", "0")
        try:
            length = int(length_value)
        except ValueError as exc:
            raise ValueError("invalid content length") from exc
        if length < 0 or length > max_bytes:
            raise ValueError("request body is too large")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body is not valid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def json_response(
        self, status: HTTPStatus, payload: dict[str, Any], *, set_cookie: str | None = None
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_security_headers()
        if set_cookie is not None:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def raw_response(
        self,
        body: bytes,
        content_type: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(HTTPStatus.OK)
        same_origin = (headers or {}).get("X-Frame-Options") == "SAMEORIGIN"
        self.send_security_headers(same_origin=same_origin)
        if (headers or {}).get("Content-Security-Policy") == PREVIEW_CSP:
            self.send_header("Content-Security-Policy", PREVIEW_CSP)
        cache_control = (
            "public, max-age=3600"
            if (headers or {}).get("Cache-Control") == "public, max-age=3600"
            else "no-store"
        )
        self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def empty_response(self, status: HTTPStatus, *, set_cookie: str | None = None) -> None:
        self.send_response(status)
        self.send_security_headers()
        if set_cookie is not None:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def error_response(self, status: HTTPStatus, code: str, message: str) -> None:
        self.json_response(status, {"error": {"code": code, "message": message}})

    def handle_service_error(self, error: ServiceError) -> None:
        if isinstance(error, ValidationError):
            return self.error_response(HTTPStatus.BAD_REQUEST, "validation_error", str(error))
        if isinstance(error, ConflictError):
            return self.error_response(HTTPStatus.CONFLICT, "conflict", str(error))
        if isinstance(error, CSRFError):
            return self.error_response(HTTPStatus.FORBIDDEN, "csrf_failed", str(error))
        if isinstance(error, SessionError):
            return self.error_response(HTTPStatus.UNAUTHORIZED, "unauthenticated", str(error))
        if isinstance(error, AuthenticationError):
            return self.error_response(HTTPStatus.UNAUTHORIZED, "unauthenticated", str(error))
        if isinstance(error, AuthorizationError):
            return self.error_response(HTTPStatus.FORBIDDEN, "forbidden", str(error))
        if isinstance(error, NotFoundError):
            return self.error_response(HTTPStatus.NOT_FOUND, "not_found", str(error))
        return self.error_response(HTTPStatus.BAD_REQUEST, "request_rejected", str(error))

    def send_security_headers(self, *, same_origin: bool = False) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "SAMEORIGIN" if same_origin else "DENY")

    @staticmethod
    def session_cookie(token: str, days: int) -> str:
        return f"{SESSION_COOKIE}={token}; Path=/; Max-Age={days * 86400}; HttpOnly; Secure; SameSite=Lax"

    @staticmethod
    def expired_session_cookie() -> str:
        return f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax"


def main() -> None:
    package_root = Path(__file__).resolve().parents[1]
    data_root = Path(os.environ.get("ARIN_DATA_DIR", package_root / "data" / "arin"))
    data_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        data_root.chmod(0o700)
    except PermissionError:
        pass

    connector_key = os.environ.get("ARIN_CONNECTOR_KEY", "")
    if not connector_key:
        raise SystemExit("ARIN_CONNECTOR_KEY is required")
    host = os.environ.get("ARIN_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("ARIN_HOST must be loopback-only")
    try:
        port = int(os.environ.get("ARIN_PORT", "8787"))
        session_days = int(os.environ.get("ARIN_SESSION_DAYS", str(SESSION_DAYS)))
    except ValueError as exc:
        raise SystemExit("ARIN_PORT and ARIN_SESSION_DAYS must be integers") from exc
    if not 1 <= session_days <= 90:
        raise SystemExit("ARIN_SESSION_DAYS must be between 1 and 90")

    ai_client = None
    ai_base_url = os.environ.get("ARIN_AI_BASE_URL", "").strip()
    ai_model = os.environ.get("ARIN_AI_MODEL", "").strip()
    if ai_base_url and ai_model:
        ai_client = OpenAICompatibleGenerator(
            ai_base_url,
            ai_model,
            os.environ.get("ARIN_AI_API_KEY", ""),
        )

    connection = db.connect(data_root / "arin.sqlite3")
    db.initialise(connection)
    service = ArinService(
        connection,
        session_days=session_days,
        asset_root=data_root / "assets",
        connector_key=connector_key,
        ai_client=ai_client,
    )
    server = ArinHTTPServer((host, port), service)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        connection.close()


if __name__ == "__main__":
    main()
