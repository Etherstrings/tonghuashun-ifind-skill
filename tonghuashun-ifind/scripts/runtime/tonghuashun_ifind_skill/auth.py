from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

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

    def resolve_tokens(self) -> tuple[TokenBundle, str]:
        bundle = self.state_store.load()
        if bundle and not bundle.is_stale():
            return bundle, "cache"
        if bundle and bundle.refresh_token:
            refreshed = self.refresh_exchange(bundle.refresh_token)
            self.state_store.save(refreshed)
            return refreshed, "refresh"
        raise RuntimeError("no valid tokens")
