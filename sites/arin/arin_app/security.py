"""Credential and token primitives for the Arin service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


PASSWORD_ITERATIONS = 310_000
PASSWORD_SALT_BYTES = 16
TOKEN_BYTES = 32
MIN_PASSWORD_LENGTH = 12


def validate_password(password: str) -> None:
    if not isinstance(password, str):
        raise ValueError("password must be text")
    if len(password) < MIN_PASSWORD_LENGTH or password.strip() != password:
        raise ValueError("password must be at least 12 characters")
    if any(ord(character) < 32 for character in password):
        raise ValueError("password contains unsupported control characters")


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )


def hash_password(password: str) -> tuple[str, str]:
    validate_password(password)
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = _derive(password, salt)
    return (
        base64.urlsafe_b64encode(digest).decode("ascii"),
        base64.urlsafe_b64encode(salt).decode("ascii"),
    )


def verify_password(password: str, encoded_hash: str, encoded_salt: str) -> bool:
    try:
        validate_password(password)
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(encoded_hash.encode("ascii"))
    except (ValueError, TypeError, UnicodeError):
        return False
    return hmac.compare_digest(_derive(password, salt), expected)


def new_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
