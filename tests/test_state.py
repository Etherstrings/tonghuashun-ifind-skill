from datetime import datetime
from datetime import timezone
from pathlib import Path

import pytest

from tonghuashun_ifind_skill.models import TokenBundle
from tonghuashun_ifind_skill.state import TokenStateStore


def test_state_store_round_trips_token_bundle(tmp_path: Path):
    store = TokenStateStore(tmp_path / "tokens.json")
    bundle = TokenBundle(
        access_token="access-demo",
        refresh_token="refresh-demo",
        expires_at="2026-04-06T12:00:00Z",
    )
    store.save(bundle)
    loaded = store.load()
    assert loaded is not None
    assert loaded.access_token == "access-demo"
    assert loaded.refresh_token == "refresh-demo"
    assert loaded.expires_at == "2026-04-06T12:00:00Z"


def test_state_store_returns_none_when_file_is_missing(tmp_path: Path):
    store = TokenStateStore(tmp_path / "tokens.json")

    assert store.load() is None


def test_state_store_returns_none_for_corrupted_json(tmp_path: Path):
    path = tmp_path / "tokens.json"
    path.write_text("{not-json", encoding="utf-8")
    store = TokenStateStore(path)

    assert store.load() is None


def test_state_store_returns_none_for_partial_state(tmp_path: Path):
    path = tmp_path / "tokens.json"
    path.write_text('{"access_token":"access-demo"}', encoding="utf-8")
    store = TokenStateStore(path)

    assert store.load() is None


def test_token_bundle_is_stale_with_timezone_aware_now():
    bundle = TokenBundle(
        access_token="access-demo",
        refresh_token="refresh-demo",
        expires_at="2026-04-06T12:00:00Z",
    )

    assert bundle.is_stale(
        now=datetime(2026, 4, 6, 11, 59, 59, tzinfo=timezone.utc)
    ) is False
    assert bundle.is_stale(
        now=datetime(2026, 4, 6, 12, 0, 0, tzinfo=timezone.utc)
    ) is True


def test_token_bundle_is_stale_accepts_naive_now():
    bundle = TokenBundle(
        access_token="access-demo",
        refresh_token="refresh-demo",
        expires_at="2026-04-06T12:00:00Z",
    )

    assert bundle.is_stale(now=datetime(2026, 4, 6, 12, 0, 1)) is True


def test_token_bundle_without_expiry_is_treated_as_stale():
    bundle = TokenBundle(
        access_token="access-demo",
        refresh_token="refresh-demo",
        expires_at=None,
    )

    assert bundle.is_stale(
        now=datetime(2026, 4, 6, 12, 0, 1, tzinfo=timezone.utc)
    ) is True


def test_token_bundle_with_invalid_expiry_is_treated_as_stale():
    bundle = TokenBundle(
        access_token="access-demo",
        refresh_token="refresh-demo",
        expires_at="not-a-datetime",
    )

    assert bundle.is_stale(
        now=datetime(2026, 4, 6, 12, 0, 1, tzinfo=timezone.utc)
    ) is True


def test_state_store_loads_invalid_expiry_as_stale_bundle(tmp_path: Path):
    path = tmp_path / "tokens.json"
    path.write_text(
        '{"access_token":"access-demo","refresh_token":"refresh-demo","expires_at":"not-a-datetime"}',
        encoding="utf-8",
    )
    store = TokenStateStore(path)

    loaded = store.load()

    assert loaded is not None
    assert loaded.is_stale(
        now=datetime(2026, 4, 6, 12, 0, 1, tzinfo=timezone.utc)
    ) is True


def test_token_bundle_from_dict_rejects_invalid_state():
    with pytest.raises(ValueError):
        TokenBundle.from_dict({"access_token": "access-demo"})
