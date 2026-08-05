"""Transactional application services for identity and workspace access."""

from __future__ import annotations

import re
import secrets
import sqlite3
import threading
import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from cryptography.fernet import Fernet

from . import db, security
from .generator import generate_project


class ServiceError(Exception):
    """Base class for errors safe to expose through the JSON API."""


class ValidationError(ServiceError):
    pass


class AuthenticationError(ServiceError):
    pass


class SessionError(AuthenticationError):
    pass


class CSRFError(SessionError):
    pass


class AuthorizationError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_DAYS = 30
MAX_FILE_BYTES = 256 * 1024
MAX_ASSET_BYTES = 5 * 1024 * 1024
MAX_CONNECTOR_CONFIG_BYTES = 32 * 1024
MAX_AGENT_MESSAGE_BYTES = 32 * 1024
MAX_AGENT_MESSAGES = 2000
SAFE_FILE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,179}$")
HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
PREVIEW_CSP = (
    "sandbox allow-scripts allow-forms; default-src 'none'; img-src data: https:; "
    "style-src 'unsafe-inline'; script-src 'unsafe-inline'"
)
ASSET_MIME_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
    "application/pdf": ".pdf",
}
CONNECTOR_KINDS = {"webhook", "rest_api", "stripe", "notion", "github"}
PROJECT_SETTING_LIMITS = {
    "title": 160,
    "description": 500,
    "seo_title": 160,
    "seo_description": 320,
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime | None = None) -> str:
    return (value or utcnow()).isoformat()


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(16)}"


def normalize_email(email: str) -> str:
    if not isinstance(email, str):
        raise ValidationError("email must be text")
    normalized = email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized) or len(normalized) > 320:
        raise ValidationError("email is invalid")
    return normalized


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValidationError("name must be text")
    normalized = " ".join(name.split())
    if not 1 <= len(normalized) <= 120:
        raise ValidationError("name is invalid")
    return normalized


def slugify(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:48] or "workspace"


def public_user(row: sqlite3.Row | dict[str, Any]) -> dict[str, str]:
    return {"id": row["id"], "email": row["email"], "name": row["name"]}


class ArinService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        session_days: int = SESSION_DAYS,
        asset_root: Path | str | None = None,
        connector_key: bytes | str | None = None,
        ai_client: Callable[[str, str], dict[str, Any]] | None = None,
    ):
        self.connection = connection
        self.session_days = session_days
        self.request_lock = threading.RLock()
        self.ai_client = ai_client
        self.asset_root = Path(asset_root) if asset_root else None
        if self.asset_root:
            self.asset_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                self.asset_root.chmod(0o700)
            except PermissionError:
                pass
        if connector_key is None:
            connector_key = Fernet.generate_key()
        if isinstance(connector_key, str):
            connector_key = connector_key.encode("ascii")
        self.connector_cipher = Fernet(connector_key)

    @staticmethod
    def hash_session_token(token: str) -> str:
        return security.hash_token(token)

    def register_user(self, email: str, name: str, password: str) -> dict[str, str]:
        normalized_email = normalize_email(email)
        normalized_name = normalize_name(name)
        try:
            password_hash, password_salt = security.hash_password(password)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        user_id = new_id("usr")
        now = timestamp()
        try:
            with db.transaction(self.connection):
                self.connection.execute(
                    """
                    INSERT INTO users
                      (id, email, name, password_hash, password_salt, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        normalized_email,
                        normalized_name,
                        password_hash,
                        password_salt,
                        now,
                        now,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("an account with that email already exists") from exc
        return {"id": user_id, "email": normalized_email, "name": normalized_name}

    def login_user(self, email: str, password: str) -> dict[str, Any]:
        normalized_email = normalize_email(email)
        row = self.connection.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (normalized_email,)
        ).fetchone()
        if row is None or not security.verify_password(
            password, row["password_hash"], row["password_salt"]
        ):
            raise AuthenticationError("email or password is incorrect")

        session_token = security.new_token()
        csrf_token = security.new_token()
        now = utcnow()
        expires = now + timedelta(days=self.session_days)
        with db.transaction(self.connection):
            self.connection.execute(
                """
                INSERT INTO sessions
                  (token_hash, user_id, csrf_token_hash, expires_at, created_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    security.hash_token(session_token),
                    row["id"],
                    security.hash_token(csrf_token),
                    timestamp(expires),
                    timestamp(now),
                    timestamp(now),
                ),
            )
        return {
            "user": public_user(row),
            "session_token": session_token,
            "csrf_token": csrf_token,
            "expires_at": timestamp(expires),
        }

    def authenticate_session(self, session_token: str, csrf_token: str) -> dict[str, Any]:
        if not session_token or not csrf_token:
            raise SessionError("session is not valid")
        row = self.connection.execute(
            """
            SELECT sessions.*, users.email, users.name
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (security.hash_token(session_token),),
        ).fetchone()
        if row is None or parse_timestamp(row["expires_at"]) <= utcnow():
            raise SessionError("session has expired")
        if not secrets.compare_digest(
            row["csrf_token_hash"], security.hash_token(csrf_token)
        ):
            raise CSRFError("request verification failed")
        now = timestamp()
        self.connection.execute(
            "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
            (now, row["token_hash"]),
        )
        return {
            "id": row["user_id"],
            "email": row["email"],
            "name": row["name"],
            "session_expires_at": row["expires_at"],
        }

    def session_from_cookie(self, session_token: str) -> dict[str, Any]:
        """Validate a cookie session and rotate its in-memory CSRF token."""

        if not session_token:
            raise SessionError("session is not valid")
        row = self.connection.execute(
            """
            SELECT sessions.*, users.email, users.name
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (security.hash_token(session_token),),
        ).fetchone()
        if row is None or parse_timestamp(row["expires_at"]) <= utcnow():
            raise SessionError("session has expired")
        csrf_token = security.new_token()
        now = timestamp()
        self.connection.execute(
            "UPDATE sessions SET csrf_token_hash = ?, last_seen_at = ? WHERE token_hash = ?",
            (security.hash_token(csrf_token), now, row["token_hash"]),
        )
        return {
            "user": {"id": row["user_id"], "email": row["email"], "name": row["name"]},
            "csrf_token": csrf_token,
            "expires_at": row["expires_at"],
        }

    def session_user(self, session_token: str) -> dict[str, str]:
        """Validate a cookie for an ordinary GET without rotating CSRF state."""

        if not session_token:
            raise SessionError("session is not valid")
        row = self.connection.execute(
            """
            SELECT sessions.expires_at, users.id, users.email, users.name
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (security.hash_token(session_token),),
        ).fetchone()
        if row is None or parse_timestamp(row["expires_at"]) <= utcnow():
            raise SessionError("session has expired")
        return {"id": row["id"], "email": row["email"], "name": row["name"]}

    def logout(self, session_token: str) -> None:
        self.connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (security.hash_token(session_token),),
        )

    def create_workspace(self, user_id: str, name: str) -> dict[str, str]:
        normalized_name = normalize_name(name)
        workspace_id = new_id("wsp")
        base_slug = slugify(normalized_name)
        slug = base_slug
        suffix = 2
        while self.connection.execute(
            "SELECT 1 FROM workspaces WHERE slug = ?", (slug,)
        ).fetchone():
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        now = timestamp()
        try:
            with db.transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO workspaces (id, name, slug, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (workspace_id, normalized_name, slug, user_id, now, now),
                )
                self.connection.execute(
                    "INSERT INTO workspace_members (workspace_id, user_id, role, created_at) VALUES (?, ?, 'owner', ?)",
                    (workspace_id, user_id, now),
                )
        except sqlite3.IntegrityError as exc:
            raise AuthorizationError("user cannot create this workspace") from exc
        return {"id": workspace_id, "name": normalized_name, "slug": slug, "role": "owner"}

    def add_workspace_member(
        self, actor_id: str, workspace_id: str, user_id: str, role: str
    ) -> dict[str, str]:
        if role not in {"editor", "viewer"}:
            raise ValidationError("role is invalid")
        self.require_membership(actor_id, workspace_id, {"owner"})
        if self.connection.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None:
            raise ValidationError("user does not exist")
        try:
            with db.transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO workspace_members (workspace_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                    (workspace_id, user_id, role, timestamp()),
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("user is already a workspace member") from exc
        return {"workspace_id": workspace_id, "user_id": user_id, "role": role}

    def require_membership(
        self, user_id: str, workspace_id: str, roles: set[str]
    ) -> dict[str, str]:
        row = self.connection.execute(
            "SELECT workspace_id, user_id, role FROM workspace_members WHERE workspace_id = ? AND user_id = ?",
            (workspace_id, user_id),
        ).fetchone()
        if row is None or row["role"] not in roles:
            raise AuthorizationError("workspace access is not allowed")
        return dict(row)

    def list_workspaces(self, user_id: str) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            SELECT workspaces.id, workspaces.name, workspaces.slug, workspace_members.role
            FROM workspaces JOIN workspace_members
              ON workspace_members.workspace_id = workspaces.id
            WHERE workspace_members.user_id = ?
            ORDER BY workspaces.created_at
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def workspace_payload(self, user_id: str, workspace_id: str) -> dict[str, Any]:
        membership = self.require_membership(user_id, workspace_id, {"owner", "editor", "viewer"})
        row = self.connection.execute("SELECT id, name, slug, owner_id, created_at, updated_at FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if row is None:
            raise NotFoundError("workspace was not found")
        payload = dict(row)
        payload["role"] = membership["role"]
        payload["members"] = self.list_workspace_members(user_id, workspace_id)
        return payload

    def list_workspace_members(self, user_id: str, workspace_id: str) -> list[dict[str, str]]:
        self.require_membership(user_id, workspace_id, {"owner", "editor", "viewer"})
        return [
            dict(row)
            for row in self.connection.execute(
                """
                SELECT users.id, users.email, users.name, workspace_members.role, workspace_members.created_at
                FROM workspace_members JOIN users ON users.id = workspace_members.user_id
                WHERE workspace_members.workspace_id = ?
                ORDER BY workspace_members.created_at, users.name
                """,
                (workspace_id,),
            ).fetchall()
        ]

    def list_projects(self, user_id: str, workspace_id: str | None = None) -> list[dict[str, Any]]:
        if workspace_id:
            self.require_membership(user_id, workspace_id, {"owner", "editor", "viewer"})
            rows = self.connection.execute(
                "SELECT * FROM projects WHERE workspace_id = ? ORDER BY updated_at DESC, id DESC",
                (workspace_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT projects.*
                FROM projects JOIN workspace_members
                  ON workspace_members.workspace_id = projects.workspace_id
                WHERE workspace_members.user_id = ?
                ORDER BY projects.updated_at DESC, projects.id DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._project_summary(row) for row in rows]

    def create_project(
        self, user_id: str, workspace_id: str, prompt: str, category: str
    ) -> dict[str, Any]:
        self.require_membership(user_id, workspace_id, {"owner", "editor"})
        generated = generate_project(prompt, category, self.ai_client)
        project_id = new_id("prj")
        project_slug = self._unique_project_slug(workspace_id, slugify(generated["name"]))
        now = timestamp()
        with db.transaction(self.connection):
            self.connection.execute(
                """
                INSERT INTO projects
                  (id, workspace_id, name, slug, prompt, category, status, settings_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
                """,
                (
                    project_id,
                    workspace_id,
                    generated["name"],
                    project_slug,
                    prompt,
                    category,
                    json.dumps({"title": generated["name"], "description": generated["summary"]}),
                    now,
                    now,
                ),
            )
            version_id = self._insert_version(project_id, user_id, generated, "build")
            self.connection.execute(
                "UPDATE projects SET current_version_id = ? WHERE id = ?",
                (version_id, project_id),
            )
            self._audit(user_id, "project.created", "project", project_id, {"category": category})
        return self.project_payload(project_id)

    def build_project(self, user_id: str, project_id: str, prompt: str) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        generated = generate_project(prompt, project["category"], self.ai_client)
        with db.transaction(self.connection):
            version_id = self._insert_version(project_id, user_id, generated, "build")
            self.connection.execute(
                "UPDATE projects SET prompt = ?, name = ?, updated_at = ?, current_version_id = ?, status = 'draft' WHERE id = ?",
                (prompt, generated["name"], timestamp(), version_id, project_id),
            )
            self._audit(user_id, "project.built", "project", project_id, {"source": generated["source"]})
        return self.project_payload(project_id)

    def list_versions(self, user_id: str, project_id: str) -> list[dict[str, Any]]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor", "viewer"})
        return [
            dict(row)
            for row in self.connection.execute(
                "SELECT id, version_number, source, created_by, created_at FROM project_versions WHERE project_id = ? ORDER BY version_number DESC",
                (project_id,),
            ).fetchall()
        ]

    def restore_version(self, user_id: str, project_id: str, version_id: str) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        version = self.connection.execute(
            "SELECT id FROM project_versions WHERE id = ? AND project_id = ?",
            (version_id, project_id),
        ).fetchone()
        if version is None:
            raise NotFoundError("project version was not found")
        files = self._files(version_id)
        generated = {
            "name": project["name"],
            "summary": project["prompt"],
            "category": project["category"],
            "source": "restore",
            "files": files,
        }
        with db.transaction(self.connection):
            restored_version_id = self._insert_version(project_id, user_id, generated, "restore")
            self.connection.execute(
                "UPDATE projects SET current_version_id = ?, status = 'draft', updated_at = ? WHERE id = ?",
                (restored_version_id, timestamp(), project_id),
            )
            self._audit(
                user_id,
                "project.version_restored",
                "project",
                project_id,
                {"source_version_id": version_id, "restored_version_id": restored_version_id},
            )
        return dict(
            self.connection.execute(
                "SELECT id, version_number, source, created_by, created_at FROM project_versions WHERE id = ?",
                (restored_version_id,),
            ).fetchone()
        )

    def update_project_settings(
        self, user_id: str, project_id: str, settings: dict[str, Any]
    ) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        if not isinstance(settings, dict):
            raise ValidationError("settings must be an object")
        try:
            merged = json.loads(project["settings_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValidationError("project settings are invalid") from exc
        if not isinstance(merged, dict):
            merged = {}

        for key, value in settings.items():
            if key not in {
                "title",
                "description",
                "primary_color",
                "accent_color",
                "seo_title",
                "seo_description",
                "logo_asset_id",
                "favicon_asset_id",
            }:
                raise ValidationError(f"setting is not supported: {key}")
            if not isinstance(value, str):
                raise ValidationError(f"setting must be text: {key}")
            value = value.strip()
            if key in PROJECT_SETTING_LIMITS and len(value) > PROJECT_SETTING_LIMITS[key]:
                raise ValidationError(f"setting is too long: {key}")
            if key == "title" and not value:
                raise ValidationError("title cannot be empty")
            if key in {"primary_color", "accent_color"} and not HEX_COLOR_PATTERN.fullmatch(value):
                raise ValidationError(f"color is invalid: {key}")
            if key.endswith("_asset_id") and value:
                self._require_project_asset(project_id, value)
            merged[key] = value

        with db.transaction(self.connection):
            self.connection.execute(
                "UPDATE projects SET settings_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(merged, separators=(",", ":")), timestamp(), project_id),
            )
            self._audit(user_id, "project.settings_updated", "project", project_id, {"keys": sorted(settings)})
        return merged

    def add_asset(
        self,
        user_id: str,
        project_id: str,
        original_name: str,
        mime_type: str,
        data: bytes,
    ) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        if self.asset_root is None:
            raise ValidationError("asset storage is not configured")
        if not isinstance(original_name, str):
            raise ValidationError("asset name must be text")
        display_name = Path(original_name.replace("\\", "/")).name.strip()
        if not display_name or len(display_name) > 200 or any(ord(char) < 32 for char in display_name):
            raise ValidationError("asset name is invalid")
        mime_type = mime_type.strip().lower() if isinstance(mime_type, str) else ""
        if mime_type not in ASSET_MIME_EXTENSIONS:
            raise ValidationError("asset type is not supported")
        if not isinstance(data, (bytes, bytearray)):
            raise ValidationError("asset content must be binary")
        data = bytes(data)
        if len(data) > MAX_ASSET_BYTES:
            raise ValidationError("asset is too large")

        asset_id = new_id("ast")
        storage_name = f"{project_id}/{secrets.token_hex(16)}{ASSET_MIME_EXTENSIONS[mime_type]}"
        asset_path = self._asset_path(storage_name)
        asset_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary_path: Path | None = None
        file_descriptor = -1
        try:
            file_descriptor, temporary_name = tempfile.mkstemp(
                prefix=".upload-", dir=str(asset_path.parent)
            )
            temporary_path = Path(temporary_name)
            os.fchmod(file_descriptor, 0o600)
            with os.fdopen(file_descriptor, "wb") as handle:
                file_descriptor = -1
                handle.write(data)
            os.replace(temporary_path, asset_path)
            temporary_path = None
            now = timestamp()
            with db.transaction(self.connection):
                self.connection.execute(
                    """
                    INSERT INTO project_assets
                      (id, project_id, original_name, storage_name, mime_type, size_bytes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (asset_id, project_id, display_name, storage_name, mime_type, len(data), now),
                )
                self._audit(
                    user_id,
                    "project.asset_added",
                    "asset",
                    asset_id,
                    {"project_id": project_id, "mime_type": mime_type, "size_bytes": len(data)},
                )
        except Exception:
            if file_descriptor >= 0:
                os.close(file_descriptor)
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()
            if asset_path.exists():
                asset_path.unlink()
            raise
        return {
            "id": asset_id,
            "project_id": project_id,
            "original_name": display_name,
            "storage_name": storage_name,
            "mime_type": mime_type,
            "size_bytes": len(data),
            "created_at": now,
            "url": f"/api/public-assets/{asset_id}",
        }

    def list_assets(self, user_id: str, project_id: str) -> list[dict[str, Any]]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor", "viewer"})
        return [self._asset_payload(row) for row in self.connection.execute(
            "SELECT * FROM project_assets WHERE project_id = ? ORDER BY created_at DESC, id DESC",
            (project_id,),
        ).fetchall()]

    def read_asset(
        self, asset_id: str, user_id: str | None = None, public: bool = False
    ) -> tuple[bytes, str, dict[str, str]]:
        row = self.connection.execute(
            """
            SELECT project_assets.*, projects.workspace_id
            FROM project_assets JOIN projects ON projects.id = project_assets.project_id
            WHERE project_assets.id = ?
            """,
            (asset_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError("asset was not found")
        if public:
            published = self.connection.execute(
                "SELECT 1 FROM deployments WHERE project_id = ? AND status = 'published' LIMIT 1",
                (row["project_id"],),
            ).fetchone()
            if published is None:
                raise NotFoundError("asset was not found")
        else:
            if user_id is None:
                raise AuthorizationError("asset access is not allowed")
            self.require_membership(user_id, row["workspace_id"], {"owner", "editor", "viewer"})
        try:
            body = self._asset_path(row["storage_name"]).read_bytes()
        except FileNotFoundError as exc:
            raise NotFoundError("asset was not found") from exc
        return body, row["mime_type"], {
            "Content-Disposition": f'inline; filename="{row["original_name"].replace(chr(34), "")}"',
            "Cache-Control": "public, max-age=3600" if public else "no-store",
        }

    def create_connector(
        self,
        user_id: str,
        project_id: str,
        kind: str,
        label: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        if kind not in CONNECTOR_KINDS:
            raise ValidationError("connector kind is not supported")
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 120:
            raise ValidationError("connector label is invalid")
        if not isinstance(config, dict):
            raise ValidationError("connector config must be an object")
        encoded = json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_CONNECTOR_CONFIG_BYTES:
            raise ValidationError("connector config is too large")
        connector_id = new_id("con")
        now = timestamp()
        with db.transaction(self.connection):
            self.connection.execute(
                """
                INSERT INTO connectors
                  (id, project_id, kind, label, config_ciphertext, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    connector_id,
                    project_id,
                    kind,
                    label.strip(),
                    self.connector_cipher.encrypt(encoded).decode("ascii"),
                    now,
                    now,
                ),
            )
            self._audit(user_id, "project.connector_created", "connector", connector_id, {"project_id": project_id, "kind": kind})
        return {
            "id": connector_id,
            "project_id": project_id,
            "kind": kind,
            "label": label.strip(),
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }

    def list_connectors(self, user_id: str, project_id: str) -> list[dict[str, Any]]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor", "viewer"})
        return [self._connector_payload(row) for row in self.connection.execute(
            "SELECT * FROM connectors WHERE project_id = ? ORDER BY created_at DESC, id DESC",
            (project_id,),
        ).fetchall()]

    def set_connector_status(self, user_id: str, connector_id: str, status: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT connectors.*, projects.workspace_id FROM connectors JOIN projects ON projects.id = connectors.project_id WHERE connectors.id = ?",
            (connector_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError("connector was not found")
        self.require_membership(user_id, row["workspace_id"], {"owner", "editor"})
        if status not in {"active", "disabled", "error"}:
            raise ValidationError("connector status is invalid")
        now = timestamp()
        with db.transaction(self.connection):
            self.connection.execute(
                "UPDATE connectors SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, connector_id),
            )
            self._audit(user_id, "project.connector_status_updated", "connector", connector_id, {"status": status})
        updated = dict(row)
        updated["status"] = status
        updated["updated_at"] = now
        return self._connector_payload(updated)

    def invite_member(
        self,
        actor_id: str,
        workspace_id: str,
        email: str,
        role: str,
        ttl_days: int = 7,
    ) -> dict[str, Any]:
        self.require_membership(actor_id, workspace_id, {"owner"})
        normalized_email = normalize_email(email)
        if role not in {"editor", "viewer"}:
            raise ValidationError("invite role is invalid")
        if not isinstance(ttl_days, int) or not 1 <= ttl_days <= 30:
            raise ValidationError("invite duration is invalid")
        token = security.new_token()
        invite_id = new_id("inv")
        now = utcnow()
        expires_at = now + timedelta(days=ttl_days)
        with db.transaction(self.connection):
            self.connection.execute(
                """
                INSERT INTO invites
                  (id, workspace_id, email, role, token_hash, expires_at, invited_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invite_id,
                    workspace_id,
                    normalized_email,
                    role,
                    security.hash_token(token),
                    timestamp(expires_at),
                    actor_id,
                    timestamp(now),
                ),
            )
            self._audit(actor_id, "workspace.invite_created", "invite", invite_id, {"workspace_id": workspace_id, "role": role})
        return {
            "id": invite_id,
            "workspace_id": workspace_id,
            "email": normalized_email,
            "role": role,
            "expires_at": timestamp(expires_at),
            "token": token,
        }

    def list_invites(self, actor_id: str, workspace_id: str) -> list[dict[str, Any]]:
        self.require_membership(actor_id, workspace_id, {"owner"})
        return [
            {
                "id": row["id"],
                "workspace_id": row["workspace_id"],
                "email": row["email"],
                "role": row["role"],
                "expires_at": row["expires_at"],
                "accepted_at": row["accepted_at"],
                "created_at": row["created_at"],
            }
            for row in self.connection.execute(
                "SELECT * FROM invites WHERE workspace_id = ? ORDER BY created_at DESC, id DESC",
                (workspace_id,),
            ).fetchall()
        ]

    def accept_invite(self, token: str, user_id: str) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise ValidationError("invite token is invalid")
        invite = self.connection.execute(
            "SELECT * FROM invites WHERE token_hash = ?", (security.hash_token(token),)
        ).fetchone()
        if invite is None:
            raise NotFoundError("invite was not found")
        if invite["accepted_at"] is not None:
            raise ConflictError("invite has already been accepted")
        if parse_timestamp(invite["expires_at"]) <= utcnow():
            raise ConflictError("invite has expired")
        user = self.connection.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise AuthenticationError("user is not valid")
        if user["email"].lower() != invite["email"].lower():
            raise AuthorizationError("invite email does not match this account")
        now = timestamp()
        try:
            with db.transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO workspace_members (workspace_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                    (invite["workspace_id"], user_id, invite["role"], now),
                )
                self.connection.execute(
                    "UPDATE invites SET accepted_at = ? WHERE id = ?",
                    (now, invite["id"]),
                )
                self._audit(user_id, "workspace.invite_accepted", "invite", invite["id"], {"workspace_id": invite["workspace_id"]})
        except sqlite3.IntegrityError as exc:
            raise ConflictError("user is already a workspace member") from exc
        return {"workspace_id": invite["workspace_id"], "user_id": user_id, "role": invite["role"]}

    def append_agent_message(
        self,
        user_id: str,
        project_id: str,
        role: str,
        content: str,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        if role not in {"user", "assistant", "system"}:
            raise ValidationError("agent message role is invalid")
        if not isinstance(content, str) or not content.strip():
            raise ValidationError("agent message is empty")
        if len(content.encode("utf-8")) > MAX_AGENT_MESSAGE_BYTES:
            raise ValidationError("agent message is too large")
        if version_id:
            version = self.connection.execute(
                "SELECT 1 FROM project_versions WHERE id = ? AND project_id = ?",
                (version_id, project_id),
            ).fetchone()
            if version is None:
                raise ValidationError("agent message version is invalid")
        message_id = new_id("msg")
        now = timestamp()
        with db.transaction(self.connection):
            self.connection.execute(
                "INSERT INTO agent_messages (id, project_id, user_id, role, content, version_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message_id, project_id, user_id, role, content, version_id, now),
            )
            old_rows = self.connection.execute(
                "SELECT id FROM agent_messages WHERE project_id = ? ORDER BY created_at ASC, id ASC",
                (project_id,),
            ).fetchall()
            for old_row in old_rows[:-MAX_AGENT_MESSAGES]:
                self.connection.execute("DELETE FROM agent_messages WHERE id = ?", (old_row["id"],))
            self._audit(user_id, "agent.message_added", "project", project_id, {"role": role, "version_id": version_id})
        return {
            "id": message_id,
            "project_id": project_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "version_id": version_id,
            "created_at": now,
        }

    def list_agent_messages(
        self, user_id: str, project_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor", "viewer"})
        limit = min(max(int(limit), 1), 100)
        return [
            dict(row)
            for row in self.connection.execute(
                "SELECT id, project_id, user_id, role, content, version_id, created_at FROM agent_messages WHERE project_id = ? ORDER BY created_at ASC, id ASC LIMIT ?",
                (project_id, limit),
            ).fetchall()
        ]

    def list_audit_events(
        self, user_id: str, project_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor", "viewer"})
        limit = min(max(int(limit), 1), 100)
        return [
            dict(row)
            for row in self.connection.execute(
                """
                SELECT id, actor_id, action, target_type, target_id, metadata_json, created_at
                FROM audit_events
                WHERE (target_type = 'project' AND target_id = ?)
                   OR target_id IN (
                     SELECT id FROM project_assets WHERE project_id = ?
                     UNION ALL
                     SELECT id FROM connectors WHERE project_id = ?
                     UNION ALL
                     SELECT id FROM invites WHERE workspace_id = ?
                   )
                ORDER BY created_at DESC, id DESC LIMIT ?
                """,
                (project_id, project_id, project_id, project["workspace_id"], limit),
            ).fetchall()
        ]

    def update_file(
        self, user_id: str, project_id: str, path: str, content: str
    ) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        safe_path = self.safe_file_path(path)
        if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValidationError("file content is too large")
        current = self._files(project["current_version_id"])
        current[safe_path] = content
        generated = {
            "name": project["name"],
            "summary": project["prompt"],
            "category": project["category"],
            "source": "edit",
            "files": current,
        }
        with db.transaction(self.connection):
            version_id = self._insert_version(project_id, user_id, generated, "edit")
            self.connection.execute(
                "UPDATE projects SET current_version_id = ?, updated_at = ?, status = 'draft' WHERE id = ?",
                (version_id, timestamp(), project_id),
            )
            self._audit(user_id, "project.file_updated", "project", project_id, {"path": safe_path})
        return dict(
            self.connection.execute(
                "SELECT id, version_number, source, created_by, created_at FROM project_versions WHERE id = ?",
                (version_id,),
            ).fetchone()
        )

    def read_preview(self, project_id: str) -> tuple[bytes, str, dict[str, str]]:
        project = self._project(project_id)
        if not project["current_version_id"]:
            raise NotFoundError("project has no version")
        return self._render_version(project["current_version_id"])

    def publish_project(self, user_id: str, project_id: str) -> dict[str, Any]:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        if not project["current_version_id"]:
            raise ValidationError("project must have a version before publishing")
        deployment_id = new_id("dpl")
        slug = f"{project['slug']}-{project_id[-8:].lower()}"
        now = timestamp()
        with db.transaction(self.connection):
            self.connection.execute(
                "UPDATE deployments SET status = 'unpublished' WHERE project_id = ? AND status = 'published'",
                (project_id,),
            )
            self.connection.execute(
                "INSERT INTO deployments (id, project_id, slug, version_id, status, created_at, published_at) VALUES (?, ?, ?, ?, 'published', ?, ?)",
                (deployment_id, project_id, slug, project["current_version_id"], now, now),
            )
            self.connection.execute(
                "UPDATE projects SET status = 'published', updated_at = ? WHERE id = ?",
                (now, project_id),
            )
            self._audit(user_id, "project.published", "project", project_id, {"slug": slug})
        return {"id": deployment_id, "project_id": project_id, "slug": slug, "status": "published"}

    def unpublish_project(self, user_id: str, project_id: str) -> None:
        project = self._project(project_id)
        self.require_membership(user_id, project["workspace_id"], {"owner", "editor"})
        with db.transaction(self.connection):
            self.connection.execute(
                "UPDATE deployments SET status = 'unpublished' WHERE project_id = ? AND status = 'published'",
                (project_id,),
            )
            self.connection.execute(
                "UPDATE projects SET status = 'draft', updated_at = ? WHERE id = ?",
                (timestamp(), project_id),
            )
            self._audit(user_id, "project.unpublished", "project", project_id, {})

    def read_published(self, slug: str) -> tuple[bytes, str, dict[str, str]]:
        row = self.connection.execute(
            "SELECT version_id FROM deployments WHERE slug = ? AND status = 'published'",
            (slug,),
        ).fetchone()
        if row is None:
            raise NotFoundError("published app was not found")
        return self._render_version(row["version_id"])

    def project_payload(self, project_id: str) -> dict[str, Any]:
        row = self._project(project_id)
        result = dict(row)
        result["settings"] = json.loads(result.pop("settings_json"))
        result["files"] = self._files(result["current_version_id"]) if result["current_version_id"] else {}
        return result

    def safe_file_path(self, path: str) -> str:
        if not isinstance(path, str) or not SAFE_FILE_PATTERN.fullmatch(path):
            raise ValidationError("file path is invalid")
        normalized = str(PurePosixPath(path))
        if normalized.startswith("../") or normalized.startswith("/") or "/../" in normalized:
            raise ValidationError("file path is invalid")
        if PurePosixPath(normalized).suffix.lower() not in {".html", ".css", ".js", ".json", ".svg", ".txt"}:
            raise ValidationError("file type is not supported")
        return normalized

    def _require_project_asset(self, project_id: str, asset_id: str) -> None:
        row = self.connection.execute(
            "SELECT 1 FROM project_assets WHERE id = ? AND project_id = ?",
            (asset_id, project_id),
        ).fetchone()
        if row is None:
            raise ValidationError("asset does not belong to this project")

    def _asset_path(self, storage_name: str) -> Path:
        if self.asset_root is None:
            raise NotFoundError("asset storage is not configured")
        root = self.asset_root.resolve()
        candidate = (root / storage_name).resolve()
        if candidate != root and root not in candidate.parents:
            raise NotFoundError("asset was not found")
        return candidate

    @staticmethod
    def _asset_payload(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "original_name": row["original_name"],
            "storage_name": row["storage_name"],
            "mime_type": row["mime_type"],
            "size_bytes": row["size_bytes"],
            "created_at": row["created_at"],
            "url": f"/api/public-assets/{row['id']}",
        }

    @staticmethod
    def _connector_payload(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "kind": row["kind"],
            "label": row["label"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _project_summary(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "workspace_id": row["workspace_id"],
            "name": row["name"],
            "slug": row["slug"],
            "prompt": row["prompt"],
            "category": row["category"],
            "status": row["status"],
            "current_version_id": row["current_version_id"],
            "settings": json.loads(row["settings_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _project(self, project_id: str) -> sqlite3.Row:
        row = self.connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            raise NotFoundError("project was not found")
        return row

    def _unique_project_slug(self, workspace_id: str, base: str) -> str:
        slug = base
        suffix = 2
        while self.connection.execute(
            "SELECT 1 FROM projects WHERE workspace_id = ? AND slug = ?", (workspace_id, slug)
        ).fetchone():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _insert_version(
        self, project_id: str, user_id: str, generated: dict[str, Any], source: str
    ) -> str:
        files = generated.get("files", {})
        if not isinstance(files, dict) or not files:
            raise ValidationError("generated project has no files")
        normalized_files: dict[str, str] = {}
        for path, content in files.items():
            safe_path = self.safe_file_path(path)
            if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_FILE_BYTES:
                raise ValidationError("generated file is too large")
            normalized_files[safe_path] = content
        row = self.connection.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 FROM project_versions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        version_number = row[0]
        version_id = new_id("ver")
        now = timestamp()
        self.connection.execute(
            "INSERT INTO project_versions (id, project_id, version_number, source, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (version_id, project_id, version_number, source, user_id, now),
        )
        for path, content in normalized_files.items():
            self.connection.execute(
                "INSERT INTO project_files (version_id, path, mime_type, content, sha256) VALUES (?, ?, ?, ?, ?)",
                (version_id, path, self._mime(path), content, hashlib.sha256(content.encode("utf-8")).hexdigest()),
            )
        return version_id

    def _files(self, version_id: str | None) -> dict[str, str]:
        if not version_id:
            return {}
        return {
            row["path"]: row["content"]
            for row in self.connection.execute(
                "SELECT path, content FROM project_files WHERE version_id = ? ORDER BY path",
                (version_id,),
            ).fetchall()
        }

    def _render_version(self, version_id: str) -> tuple[bytes, str, dict[str, str]]:
        files = self._files(version_id)
        html_file = files.get("index.html")
        if html_file is None:
            raise NotFoundError("project entrypoint was not found")
        css = files.get("styles.css", "")
        js = files.get("app.js", "")
        rendered = html_file.replace(
            '<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>"
        ).replace('<script src="app.js"></script>', f"<script>{js}</script>")
        return rendered.encode("utf-8"), "text/html; charset=utf-8", {
            "Content-Security-Policy": PREVIEW_CSP,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Cache-Control": "no-store",
        }

    @staticmethod
    def _mime(path: str) -> str:
        return {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
            ".txt": "text/plain; charset=utf-8",
        }[PurePosixPath(path).suffix.lower()]

    def _audit(self, actor_id: str, action: str, target_type: str, target_id: str, metadata: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO audit_events (id, actor_id, action, target_type, target_id, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id("aud"), actor_id, action, target_type, target_id, json.dumps(metadata, separators=(",", ":")), timestamp()),
        )
