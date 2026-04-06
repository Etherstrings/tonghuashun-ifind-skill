from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Mapping
from typing import Protocol

from tonghuashun_ifind_skill.models import TokenBundle


@dataclass(slots=True)
class TokenCapture:
    response_candidates: list[Mapping[str, Any]]
    request_header_candidates: list[Mapping[str, Any]]
    storage_candidates: list[Mapping[str, Any]]
    cookie_candidates: list[Mapping[str, Any]]


class BrowserLoginAdapter(Protocol):
    def login_and_collect(self, username: str, password: str) -> TokenCapture:
        ...


@dataclass(slots=True)
class TokenCandidate:
    access_token: str | None
    refresh_token: str | None
    expires_at: str | None


class BrowserLoginRunner:
    def __init__(self, adapter: BrowserLoginAdapter) -> None:
        self.adapter = adapter

    def login_and_capture(self, username: str, password: str) -> TokenBundle:
        capture = self.adapter.login_and_collect(username, password)
        return extract_token_bundle(
            response_candidates=capture.response_candidates,
            request_header_candidates=capture.request_header_candidates,
            storage_candidates=capture.storage_candidates,
            cookie_candidates=capture.cookie_candidates,
        )


class PlaywrightLoginAdapter:
    def __init__(
        self,
        *,
        login_url: str,
        username_selector: str,
        password_selector: str,
        submit_selector: str,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        self.login_url = login_url
        self.username_selector = username_selector
        self.password_selector = password_selector
        self.submit_selector = submit_selector
        self.headless = headless
        self.timeout_ms = timeout_ms

    def login_and_collect(self, username: str, password: str) -> TokenCapture:
        from playwright.sync_api import sync_playwright

        response_payloads: list[Mapping[str, Any]] = []
        request_headers: list[Mapping[str, Any]] = []
        storage_candidates: list[Mapping[str, Any]] = []
        cookie_candidates: list[Mapping[str, Any]] = []

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            def handle_response(response: Any) -> None:
                try:
                    payload = response.json()
                except Exception:
                    return
                if isinstance(payload, dict):
                    response_payloads.append(payload)

            def handle_request(request: Any) -> None:
                headers = request.headers
                if isinstance(headers, dict):
                    request_headers.append(headers)

            page.on("response", handle_response)
            page.on("request", handle_request)

            page.goto(self.login_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.fill(self.username_selector, username)
            page.fill(self.password_selector, password)
            page.click(self.submit_selector)
            page.wait_for_load_state("networkidle", timeout=self.timeout_ms)

            storage_snapshot = page.evaluate(
                """() => {
                    const snapshot = { localStorage: {}, sessionStorage: {} };
                    try {
                        const local = window.localStorage;
                        for (let i = 0; i < local.length; i += 1) {
                            const key = local.key(i);
                            snapshot.localStorage[key] = local.getItem(key);
                        }
                    } catch (_) {}
                    try {
                        const session = window.sessionStorage;
                        for (let i = 0; i < session.length; i += 1) {
                            const key = session.key(i);
                            snapshot.sessionStorage[key] = session.getItem(key);
                        }
                    } catch (_) {}
                    return snapshot;
                }""",
            )

            if isinstance(storage_snapshot, dict):
                local_storage = storage_snapshot.get("localStorage")
                session_storage = storage_snapshot.get("sessionStorage")
                if isinstance(local_storage, dict):
                    storage_candidates.append(local_storage)
                if isinstance(session_storage, dict):
                    storage_candidates.append(session_storage)

            cookies = context.cookies()
            for cookie in cookies:
                name = cookie.get("name")
                value = cookie.get("value")
                if isinstance(name, str) and isinstance(value, str):
                    cookie_candidates.append({name: value})

            context.close()
            browser.close()

        return TokenCapture(
            response_candidates=response_payloads,
            request_header_candidates=request_headers,
            storage_candidates=storage_candidates,
            cookie_candidates=cookie_candidates,
        )


def extract_token_bundle(
    *,
    response_candidates: list[Mapping[str, Any]],
    request_header_candidates: list[Mapping[str, Any]],
    storage_candidates: list[Mapping[str, Any]],
    cookie_candidates: list[Mapping[str, Any]],
) -> TokenBundle:
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None

    for candidates in (
        response_candidates,
        request_header_candidates,
        storage_candidates,
        cookie_candidates,
    ):
        for candidate in candidates:
            token_candidate = _extract_candidate(candidate)
            if access_token is None and token_candidate.access_token:
                access_token = token_candidate.access_token
            if refresh_token is None and token_candidate.refresh_token:
                refresh_token = token_candidate.refresh_token
            if expires_at is None and token_candidate.expires_at:
                expires_at = token_candidate.expires_at
            if access_token and refresh_token:
                break
        if access_token and refresh_token:
            break

    if not access_token or not refresh_token:
        raise ValueError("unable to extract token bundle from browser capture")

    return TokenBundle(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


_ACCESS_KEYS = ("access_token", "accessToken")
_REFRESH_KEYS = ("refresh_token", "refreshToken")
_EXPIRES_AT_KEYS = ("expires_at", "expiresAt")
_EXPIRES_IN_KEYS = ("expires_in", "expiresIn")


def _extract_candidate(candidate: Mapping[str, Any]) -> TokenCandidate:
    access_token = _first_text(candidate, _ACCESS_KEYS)
    refresh_token = _first_text(candidate, _REFRESH_KEYS)
    expires_at = _first_text(candidate, _EXPIRES_AT_KEYS)
    if expires_at is None:
        expires_at = _expires_at_from_seconds(candidate)
    return TokenCandidate(access_token, refresh_token, expires_at)


def _first_text(candidate: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _expires_at_from_seconds(candidate: Mapping[str, Any]) -> str | None:
    for key in _EXPIRES_IN_KEYS:
        value = candidate.get(key)
        seconds = _coerce_int(value)
        if seconds is None:
            continue
        expires_at = datetime.now(UTC) + timedelta(seconds=seconds)
        return expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return None


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None
