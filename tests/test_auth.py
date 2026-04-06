import pytest

from tonghuashun_ifind_skill.auth import AuthManager
from tonghuashun_ifind_skill.models import TokenBundle


def test_auth_manager_reuses_unexpired_access_token(tmp_path):
    manager = AuthManager.for_test(
        state_path=tmp_path / "tokens.json",
        refresh_exchange=lambda refresh_token: (_ for _ in ()).throw(
            AssertionError("should not refresh")
        ),
        browser_login=lambda: (_ for _ in ()).throw(
            AssertionError("should not login")
        ),
    )
    manager.state_store.save(
        TokenBundle("access-demo", "refresh-demo", "2099-01-01T00:00:00Z")
    )

    bundle, source = manager.resolve_tokens()

    assert bundle.access_token == "access-demo"
    assert source == "cache"


def test_auth_manager_refreshes_stale_access_token(tmp_path):
    refreshed = TokenBundle(
        access_token="access-new",
        refresh_token="refresh-new",
        expires_at="2099-01-01T00:00:00Z",
    )
    manager = AuthManager.for_test(
        state_path=tmp_path / "tokens.json",
        refresh_exchange=lambda refresh_token: refreshed
        if refresh_token == "refresh-demo"
        else (_ for _ in ()).throw(AssertionError("unexpected refresh token")),
        browser_login=lambda: (_ for _ in ()).throw(
            AssertionError("should not login")
        ),
    )
    manager.state_store.save(
        TokenBundle("access-demo", "refresh-demo", "2000-01-01T00:00:00Z")
    )

    bundle, source = manager.resolve_tokens()

    assert bundle.access_token == "access-new"
    assert source == "refresh"
    persisted = manager.state_store.load()
    assert persisted is not None
    assert persisted.access_token == "access-new"


def test_auth_manager_calls_browser_login_when_no_cached_tokens(tmp_path):
    captured = {}
    manager = AuthManager.for_test(
        state_path=tmp_path / "tokens.json",
        refresh_exchange=lambda refresh_token: (_ for _ in ()).throw(
            AssertionError("should not refresh")
        ),
        browser_login=lambda: captured.setdefault(
            "bundle",
            TokenBundle("access-login", "refresh-login", "2099-01-01T00:00:00Z"),
        ),
    )

    bundle, source = manager.resolve_tokens()

    assert bundle.access_token == "access-login"
    assert source == "playwright"
    persisted = manager.state_store.load()
    assert persisted is not None
    assert persisted.access_token == "access-login"


def test_auth_manager_calls_browser_login_when_stale_without_refresh_token(
    tmp_path,
):
    captured = {}
    manager = AuthManager.for_test(
        state_path=tmp_path / "tokens.json",
        refresh_exchange=lambda refresh_token: (_ for _ in ()).throw(
            AssertionError("should not refresh")
        ),
        browser_login=lambda: captured.setdefault(
            "bundle",
            TokenBundle("access-login", "refresh-login", "2099-01-01T00:00:00Z"),
        ),
    )
    manager.state_store.save(TokenBundle("access-demo", "", "2000-01-01T00:00:00Z"))

    bundle, source = manager.resolve_tokens()

    assert bundle.access_token == "access-login"
    assert source == "playwright"
    persisted = manager.state_store.load()
    assert persisted is not None
    assert persisted.access_token == "access-login"


def test_auth_manager_falls_back_to_browser_login_on_refresh_failure(tmp_path):
    captured = {}
    manager = AuthManager.for_test(
        state_path=tmp_path / "tokens.json",
        refresh_exchange=lambda refresh_token: (_ for _ in ()).throw(
            ValueError("refresh failed")
        ),
        browser_login=lambda: captured.setdefault(
            "bundle",
            TokenBundle("access-login", "refresh-login", "2099-01-01T00:00:00Z"),
        ),
    )
    manager.state_store.save(
        TokenBundle("access-demo", "refresh-demo", "2000-01-01T00:00:00Z")
    )

    bundle, source = manager.resolve_tokens()

    assert bundle.access_token == "access-login"
    assert source == "playwright"
    persisted = manager.state_store.load()
    assert persisted is not None
    assert persisted.access_token == "access-login"
