"""Tests for token-based authentication, CSRF, and queue scoping.

These tests do NOT require a Redis instance — they test the auth middleware,
permission logic, and CSRF enforcement using a mock dashboard that stubs out
the Redis-dependent routes.
"""

import tempfile

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.testclient import TestClient

from rq_dashboard_fast.utils.auth import (
    AuthConfig,
    TokenPermissions,
    generate_csrf_token,
    generate_token_pair,
    hash_token,
    queue_allowed,
)

# ---------------------------------------------------------------------------
# Unit tests for auth utilities
# ---------------------------------------------------------------------------


class TestHashToken:
    def test_deterministic(self):
        assert hash_token("abc") == hash_token("abc")

    def test_different_inputs(self):
        assert hash_token("abc") != hash_token("def")


class TestGenerateTokenPair:
    def test_pair_matches(self):
        token, token_hash = generate_token_pair()
        assert hash_token(token) == token_hash

    def test_unique(self):
        t1, _ = generate_token_pair()
        t2, _ = generate_token_pair()
        assert t1 != t2


class TestQueueAllowed:
    def test_wildcard(self):
        assert queue_allowed("anything", ["*"]) is True

    def test_explicit_match(self):
        assert queue_allowed("emails", ["emails", "notifications"]) is True

    def test_no_match(self):
        assert queue_allowed("payments", ["emails", "notifications"]) is False

    def test_empty_list(self):
        assert queue_allowed("anything", []) is False


class TestTokenPermissions:
    def test_defaults_are_least_privilege(self):
        p = TokenPermissions()
        assert p.authenticated is False
        assert p.queues == []
        assert p.access == "read"


class TestAuthConfig:
    def test_disabled_when_no_path(self):
        config = AuthConfig(None)
        assert config.enabled is False

    def test_disabled_when_file_missing(self):
        config = AuthConfig("/nonexistent/path/auth.yaml")
        assert config.enabled is False

    def test_disabled_when_no_tokens_key(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("something_else: true\n")
            f.flush()
            config = AuthConfig(f.name)
        assert config.enabled is False

    def test_disabled_when_tokens_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("tokens: []\n")
            f.flush()
            config = AuthConfig(f.name)
        assert config.enabled is False

    def test_disabled_when_tokens_have_blank_hashes(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write('tokens:\n  - hash: ""\n    queues: ["*"]\n')
            f.flush()
            config = AuthConfig(f.name)
        assert config.enabled is False

    def test_enabled_with_valid_token(self):
        token, token_hash = generate_token_pair()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                f'tokens:\n  - hash: "{token_hash}"\n    queues: ["*"]\n    access: admin\n'
            )
            f.flush()
            config = AuthConfig(f.name)
        assert config.enabled is True
        entry = config.resolve_hash(token_hash)
        assert entry is not None
        assert entry["queues"] == ["*"]
        assert entry["access"] == "admin"

    def test_resolve_unknown_hash(self):
        token, token_hash = generate_token_pair()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(f'tokens:\n  - hash: "{token_hash}"\n    queues: ["*"]\n')
            f.flush()
            config = AuthConfig(f.name)
        assert config.resolve_hash("nonexistent") is None

    def test_defaults_access_to_read(self):
        token, token_hash = generate_token_pair()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(f'tokens:\n  - hash: "{token_hash}"\n    queues: ["*"]\n')
            f.flush()
            config = AuthConfig(f.name)
        entry = config.resolve_hash(token_hash)
        assert entry["access"] == "read"

    def test_title_is_optional(self):
        token, token_hash = generate_token_pair()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(f'tokens:\n  - hash: "{token_hash}"\n    queues: ["*"]\n')
            f.flush()
            config = AuthConfig(f.name)
        entry = config.resolve_hash(token_hash)
        assert entry["title"] is None


# ---------------------------------------------------------------------------
# Integration tests using a minimal FastAPI app with auth middleware
# ---------------------------------------------------------------------------


def _make_auth_yaml(tokens: list[dict]) -> str:
    """Write a temporary auth YAML file and return its path."""
    import yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"tokens": tokens}, f)
        return f.name


def _make_app(auth_config: str = None):
    """Create a minimal FastAPI app with auth middleware but no Redis dependency."""
    from rq_dashboard_fast.rq_dashboard_fast import RedisQueueDashboard

    app = FastAPI()
    # We create the dashboard but only use it for middleware / auth routes.
    # Actual Redis-dependent routes will 500, but we test auth behavior before
    # those routes are reached.
    dashboard = RedisQueueDashboard(
        redis_url="redis://localhost:6379",
        prefix="",
        auth_config=auth_config,
    )
    app.mount("", dashboard)
    return app


@pytest.fixture
def admin_token():
    token, token_hash = generate_token_pair()
    return token, token_hash


@pytest.fixture
def read_token():
    token, token_hash = generate_token_pair()
    return token, token_hash


class TestNoAuthMode:
    """When no auth config is provided, everything should be open."""

    def test_pages_accessible(self):
        app = _make_app()
        client = TestClient(app, follow_redirects=False)
        # /login should not be needed — middleware passes through
        response = client.get("/queues/json")
        # May 500 due to no Redis, but should NOT be 302 to login
        assert response.status_code != 302

    def test_mutations_allowed_without_csrf(self):
        app = _make_app()
        client = TestClient(app, follow_redirects=False)
        # Will 500 because no Redis, but should not be 403 (no CSRF required)
        response = client.delete("/queues/testqueue")
        assert response.status_code != 403


class TestTokenExchange:
    """Test the ?token= → cookie → redirect flow."""

    def test_valid_token_sets_cookie_and_redirects(self, admin_token):
        token, token_hash = admin_token
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": ["*"], "access": "admin"}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        response = client.get(f"/?token={token}")
        assert response.status_code == 302
        # Token should be stripped from redirect URL
        location = response.headers["location"]
        assert "token=" not in location
        # Cookies should be set
        assert "rq_dash_token" in response.cookies
        assert "rq_dash_csrf" in response.cookies

    def test_valid_token_preserves_other_params(self, admin_token):
        token, token_hash = admin_token
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": ["*"], "access": "admin"}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        response = client.get(f"/jobs?token={token}&state=failed&queue_name=emails")
        location = response.headers["location"]
        assert "token=" not in location
        assert "state=failed" in location
        assert "queue_name=emails" in location

    def test_invalid_token_redirects_to_login(self):
        token, token_hash = generate_token_pair()
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": ["*"], "access": "admin"}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        response = client.get("/?token=bogus-token")
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_no_token_no_cookie_redirects_to_login(self, admin_token):
        _, token_hash = admin_token
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": ["*"], "access": "admin"}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        response = client.get("/queues")
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_login_page_accessible(self, admin_token):
        _, token_hash = admin_token
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": ["*"], "access": "admin"}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        response = client.get("/login")
        assert response.status_code == 200
        assert "Access Token" in response.text


class TestCsrfProtection:
    """CSRF token must be present on mutation requests when auth is enabled."""

    def _get_authenticated_client(self, token, token_hash):
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": ["*"], "access": "admin"}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        # Exchange token for cookies
        response = client.get(f"/?token={token}")
        assert response.status_code == 302
        csrf_token = response.cookies.get("rq_dash_csrf")
        return client, csrf_token

    def test_mutation_without_csrf_rejected(self, admin_token):
        token, token_hash = admin_token
        client, _ = self._get_authenticated_client(token, token_hash)

        # DELETE without CSRF header should be rejected
        response = client.delete("/queues/testqueue")
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    def test_mutation_with_wrong_csrf_rejected(self, admin_token):
        token, token_hash = admin_token
        client, _ = self._get_authenticated_client(token, token_hash)

        response = client.delete(
            "/queues/testqueue", headers={"X-CSRF-Token": "wrong-token"}
        )
        assert response.status_code == 403

    def test_mutation_with_valid_csrf_accepted(self, admin_token):
        token, token_hash = admin_token
        client, csrf_token = self._get_authenticated_client(token, token_hash)

        # With correct CSRF, the request should pass auth (may 500 due to no Redis)
        response = client.delete(
            "/queues/testqueue", headers={"X-CSRF-Token": csrf_token}
        )
        # Should NOT be 403 — it passed auth/CSRF. 500 is expected (no Redis).
        assert response.status_code != 403

    def test_get_requests_dont_need_csrf(self, admin_token):
        token, token_hash = admin_token
        client, _ = self._get_authenticated_client(token, token_hash)

        # GET requests should not require CSRF
        response = client.get("/queues/json")
        assert response.status_code != 403


class TestQueueScoping:
    """Read tokens should only see their allowed queues."""

    def _get_authenticated_client(self, token, token_hash, queues, access="read"):
        config_path = _make_auth_yaml(
            [{"hash": token_hash, "queues": queues, "access": access}]
        )
        app = _make_app(config_path)
        client = TestClient(app, follow_redirects=False)

        response = client.get(f"/?token={token}")
        csrf_token = response.cookies.get("rq_dash_csrf")
        return client, csrf_token

    def test_read_access_blocks_mutations(self, read_token):
        token, token_hash = read_token
        client, csrf_token = self._get_authenticated_client(
            token, token_hash, ["*"], access="read"
        )

        response = client.delete(
            "/queues/testqueue", headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_admin_scoped_queue_blocks_other_queues(self, admin_token):
        token, token_hash = admin_token
        client, csrf_token = self._get_authenticated_client(
            token, token_hash, ["emails"], access="admin"
        )

        # Deleting a queue not in the allowed list should be 403
        response = client.delete(
            "/queues/payments", headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_admin_scoped_queue_allows_own_queue(self, admin_token):
        token, token_hash = admin_token
        client, csrf_token = self._get_authenticated_client(
            token, token_hash, ["testqueue"], access="admin"
        )

        # Deleting an allowed queue should pass auth (may 500 due to no Redis)
        response = client.delete(
            "/queues/testqueue", headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code != 403


class TestCustomTitle:
    """Token with a title should pass it through to templates."""

    def test_title_in_config(self):
        token, token_hash = generate_token_pair()
        config_path = _make_auth_yaml(
            [
                {
                    "hash": token_hash,
                    "queues": ["*"],
                    "access": "admin",
                    "title": "My Dashboard",
                }
            ]
        )
        config = AuthConfig(config_path)
        entry = config.resolve_hash(token_hash)
        assert entry["title"] == "My Dashboard"
