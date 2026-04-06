from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from tonghuashun_ifind_skill.models import TokenBundle
from tonghuashun_ifind_skill.state import TokenStateStore


class AuthManager:
    def __init__(
        self,
        *,
        state_store: TokenStateStore,
        refresh_exchange: Callable[[str], TokenBundle],
        browser_login: Callable[[], TokenBundle],
    ) -> None:
        self.state_store = state_store
        self.refresh_exchange = refresh_exchange
        self.browser_login = browser_login

    @classmethod
    def for_test(
        cls,
        *,
        state_path: Path,
        refresh_exchange: Callable[[str], TokenBundle],
        browser_login: Callable[[], TokenBundle],
    ) -> "AuthManager":
        return cls(
            state_store=TokenStateStore(state_path),
            refresh_exchange=refresh_exchange,
            browser_login=browser_login,
        )

    def resolve_tokens(self) -> tuple[TokenBundle, Literal["cache", "refresh"]]:
        bundle = self.state_store.load()
        if bundle is None:
            raise RuntimeError("no cached tokens")
        if not bundle.is_stale():
            return bundle, "cache"
        if not bundle.refresh_token:
            raise RuntimeError("stale tokens without refresh")
        try:
            refreshed = self.refresh_exchange(bundle.refresh_token)
        except Exception as exc:
            raise RuntimeError("refresh exchange failed") from exc
        self.state_store.save(refreshed)
        return refreshed, "refresh"
