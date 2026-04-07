from types import ModuleType
import sys

from tonghuashun_ifind_skill.browser_login import PlaywrightLoginAdapter
from tonghuashun_ifind_skill.browser_login import extract_token_bundle
from tonghuashun_ifind_skill.browser_login import resolve_browser_executable


def test_extract_token_bundle_prefers_response_payload_over_storage():
    bundle = extract_token_bundle(
        response_candidates=[{"access_token": "access-a", "refresh_token": "refresh-a"}],
        request_header_candidates=[],
        storage_candidates=[{"access_token": "access-b", "refresh_token": "refresh-b"}],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-a"
    assert bundle.refresh_token == "refresh-a"


def test_extract_token_bundle_handles_nested_response_payload():
    bundle = extract_token_bundle(
        response_candidates=[
            {
                "data": {
                    "access_token": "access-nested",
                    "refresh_token": "refresh-nested",
                    "expires_in": 3600,
                }
            }
        ],
        request_header_candidates=[],
        storage_candidates=[],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-nested"
    assert bundle.refresh_token == "refresh-nested"
    assert bundle.expires_at is not None


def test_extract_token_bundle_combines_across_priority_buckets():
    bundle = extract_token_bundle(
        response_candidates=[{"access_token": "access-top"}],
        request_header_candidates=[],
        storage_candidates=[{"refresh_token": "refresh-lower"}],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-top"
    assert bundle.refresh_token == "refresh-lower"


def test_extract_token_bundle_parses_json_string_storage_values():
    bundle = extract_token_bundle(
        response_candidates=[],
        request_header_candidates=[],
        storage_candidates=[
            {
                "token_payload": (
                    '{"access_token": "access-json", "refresh_token": "refresh-json"}'
                )
            }
        ],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-json"
    assert bundle.refresh_token == "refresh-json"


def test_extract_token_bundle_carries_expiry_from_later_candidate():
    bundle = extract_token_bundle(
        response_candidates=[
            {"access_token": "access-early", "refresh_token": "refresh-early"},
            {"expires_in": 3600},
        ],
        request_header_candidates=[],
        storage_candidates=[],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-early"
    assert bundle.refresh_token == "refresh-early"
    assert bundle.expires_at is not None


def test_resolve_browser_executable_uses_local_candidate(monkeypatch, tmp_path):
    chrome_path = tmp_path / "Google Chrome"
    chrome_path.write_text("")
    monkeypatch.delenv("IFIND_BROWSER_EXECUTABLE", raising=False)
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.browser_login.DEFAULT_BROWSER_EXECUTABLES",
        (chrome_path,),
    )

    assert resolve_browser_executable() == str(chrome_path)


def test_playwright_login_adapter_launches_with_resolved_browser_path(
    monkeypatch,
    tmp_path,
):
    chrome_path = tmp_path / "Google Chrome"
    chrome_path.write_text("")
    launch_kwargs: dict[str, object] = {}

    class FakePage:
        def on(self, _event: str, _handler: object) -> None:
            return None

        def goto(self, *_args: object, **_kwargs: object) -> None:
            return None

        def fill(self, *_args: object, **_kwargs: object) -> None:
            return None

        def click(self, *_args: object, **_kwargs: object) -> None:
            return None

        def wait_for_load_state(self, *_args: object, **_kwargs: object) -> None:
            return None

        def evaluate(self, _script: str) -> dict[str, dict[str, str]]:
            return {"localStorage": {}, "sessionStorage": {}}

    class FakeContext:
        def new_page(self) -> FakePage:
            return FakePage()

        def cookies(self) -> list[dict[str, str]]:
            return []

        def close(self) -> None:
            return None

    class FakeBrowser:
        def new_context(self) -> FakeContext:
            return FakeContext()

        def close(self) -> None:
            return None

    class FakeChromium:
        def launch(self, **kwargs: object) -> FakeBrowser:
            launch_kwargs.update(kwargs)
            return FakeBrowser()

    class FakePlaywrightContext:
        def __enter__(self) -> object:
            return type("FakePlaywright", (), {"chromium": FakeChromium()})()

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    fake_sync_api = ModuleType("playwright.sync_api")
    fake_sync_api.sync_playwright = lambda: FakePlaywrightContext()
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_sync_api)
    monkeypatch.delenv("IFIND_BROWSER_EXECUTABLE", raising=False)
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.browser_login.DEFAULT_BROWSER_EXECUTABLES",
        (chrome_path,),
    )

    adapter = PlaywrightLoginAdapter(
        login_url="https://example.com/login",
        username_selector="#username",
        password_selector="#password",
        submit_selector="#submit",
    )

    capture = adapter.login_and_collect("alice", "secret")

    assert capture.response_candidates == []
    assert launch_kwargs["executable_path"] == str(chrome_path)
    assert launch_kwargs["headless"] is True
