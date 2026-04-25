from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Literal

import requests

from tonghuashun_ifind_skill.models import TokenBundle
from tonghuashun_ifind_skill.models import format_timestamp
from tonghuashun_ifind_skill.state import TokenStateStore


class AuthManager:
    def __init__(
        self,
        *,
        state_store: TokenStateStore,
        refresh_exchange: Callable[[str], TokenBundle],
    ) -> None:
        self.state_store = state_store
        self.refresh_exchange = refresh_exchange

    @classmethod
    def for_test(
        cls,
        *,
        state_path: Path,
        refresh_exchange: Callable[[str], TokenBundle],
    ) -> "AuthManager":
        return cls(
            state_store=TokenStateStore(state_path),
            refresh_exchange=refresh_exchange,
        )

    @classmethod
    def create(
        cls,
        *,
        state_path: Path,
        refresh_exchange: Callable[[str], TokenBundle],
    ) -> "AuthManager":
        return cls(
            state_store=TokenStateStore(state_path),
            refresh_exchange=refresh_exchange,
        )

    def resolve_tokens(
        self,
    ) -> tuple[TokenBundle, Literal["cache", "refresh"]]:
        bundle = self.state_store.load()
        if bundle is not None and not bundle.is_stale():
            return bundle, "cache"

        if bundle is None:
            raise RuntimeError(
                "missing iFinD token state; run auth-set-refresh-token with "
                "the refresh_token from iFinD Super Command"
            )

        if not bundle.refresh_token:
            raise RuntimeError(
                "cached iFinD token state has no refresh_token; run "
                "auth-set-refresh-token"
            )

        try:
            refreshed = self.refresh_exchange(bundle.refresh_token)
        except Exception:
            raise RuntimeError(
                "failed to exchange iFinD refresh_token for access_token"
            )
        self.state_store.save(refreshed)
        return refreshed, "refresh"


def exchange_refresh_token(
    refresh_token: str,
    *,
    base_url: str,
    timeout: float = 10.0,
    now: Callable[[], datetime] | None = None,
) -> TokenBundle:
    response = requests.post(
        f"{base_url.rstrip('/')}/get_access_token",
        json={},
        headers={"Content-Type": "application/json", "refresh_token": refresh_token},
        timeout=timeout,
    )
    response.raise_for_status()

    access_token, expires_in = _parse_refresh_payload(response.json())
    return TokenBundle(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=_resolve_refresh_expiry(expires_in, now=now),
    )


def _parse_refresh_payload(payload: object) -> tuple[str, int]:
    if not isinstance(payload, dict):
        raise ValueError("iFinD auth response must be a JSON object")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("iFinD auth response missing data object")

    access_token = data.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise ValueError("iFinD auth response missing access_token")

    expires_in_raw = data.get("expires_in", 0)
    try:
        expires_in = int(expires_in_raw)
    except (TypeError, ValueError):
        expires_in = 0
    return access_token, expires_in


def _resolve_refresh_expiry(
    expires_in: int,
    *,
    now: Callable[[], datetime] | None = None,
) -> str:
    current = now() if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)
    expires_at = current + timedelta(seconds=max(expires_in - 30, 0))
    return format_timestamp(expires_at)
