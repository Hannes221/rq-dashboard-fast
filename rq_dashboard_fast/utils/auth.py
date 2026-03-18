import hashlib
import logging
import secrets
import uuid
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

COOKIE_NAME = "rq_dash_token"
CSRF_COOKIE_NAME = "rq_dash_csrf"


class TokenPermissions(BaseModel):
    authenticated: bool = False
    queues: list[str] = []
    access: str = "read"
    title: Optional[str] = None
    csrf_token: Optional[str] = None
    allow_workers: bool = True
    allow_export: bool = True


class AuthConfig:
    """Loads and resolves token-based auth from a YAML config file."""

    def __init__(self, config_path: Optional[str] = None):
        self.enabled = False
        self._tokens: dict[str, dict] = {}

        if config_path is None:
            return

        path = Path(config_path)
        if not path.exists():
            logger.warning(
                "Auth config file not found: %s — auth disabled", config_path
            )
            return

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except Exception:
            logger.exception("Failed to load auth config from %s", config_path)
            return

        if not data or "tokens" not in data:
            logger.warning("Auth config has no 'tokens' key — auth disabled")
            return

        for entry in data["tokens"]:
            h = entry.get("hash", "").strip()
            if not h:
                continue
            self._tokens[h] = {
                "queues": entry.get("queues", ["*"]),
                "access": entry.get("access", "read"),
                "title": entry.get("title"),
                "allow_workers": entry.get("allow_workers", True),
                "allow_export": entry.get("allow_export", True),
            }

        if not self._tokens:
            logger.warning("Auth config has no valid tokens — auth disabled")
            return

        self.enabled = True
        logger.info("Auth enabled with %d token(s)", len(self._tokens))

    def resolve_hash(self, token_hash: str) -> Optional[dict]:
        return self._tokens.get(token_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def generate_token_pair() -> tuple[str, str]:
    token = str(uuid.uuid4())
    return token, hash_token(token)


def queue_allowed(queue_name: str, allowed_queues: list[str]) -> bool:
    if "*" in allowed_queues:
        return True
    return queue_name in allowed_queues


def worker_visible(worker_queues: list[str], allowed_queues: list[str]) -> bool:
    """Return True if a worker shares at least one queue with the allowed list."""
    if "*" in allowed_queues:
        return True
    return bool(set(worker_queues) & set(allowed_queues))
