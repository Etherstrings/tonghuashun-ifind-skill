# TongHuaShun iFinD Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standard OpenClaw skill that can obtain iFinD tokens with headless Playwright, fall back to manual token injection, and call arbitrary iFinD OpenAPI endpoints through a raw-first API contract plus a few thin wrappers.

**Architecture:** Keep the project as a small skill repository. Put all OpenClaw-facing behavior inside the `tonghuashun-ifind/` skill directory, and keep the implementation in a small Python runtime under `tonghuashun_ifind_skill`. The main command path is `api-call(endpoint, payload)`, while `basic-data`, `smart-pick`, `report-query`, and `date-sequence` are lightweight aliases over the same client and auth stack.

**Tech Stack:** Python 3.12, requests, Playwright for Python, pytest, shell install/validation scripts, OpenClaw skill packaging conventions.

---

## File Map

**Create:**

- `pyproject.toml`  
  Python package metadata, runtime dependencies, pytest configuration, and optional CLI entry point.
- `.gitignore`  
  Ignore Python caches, Playwright outputs, token state fixtures, and local virtualenv files.
- `README.md`  
  Repo-level quickstart, local validation, token flow, and publish notes.
- `scripts/install_skill.sh`  
  Copy `tonghuashun-ifind/` into `~/.openclaw/workspace/skills/tonghuashun-ifind`.
- `scripts/validate_skill.sh`  
  Run focused tests and basic CLI smoke checks.
- `tonghuashun-ifind/SKILL.md`  
  OpenClaw-facing skill contract and invocation guidance.
- `tonghuashun-ifind/agents/openai.yaml`  
  Agent metadata for the skill package.
- `tonghuashun-ifind/references/usage.md`  
  Compact usage reference for commands and expected inputs.
- `tonghuashun-ifind/scripts/ifind_cli.py`  
  Script entrypoint invoked by the skill.
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/__init__.py`  
  Runtime package marker.
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/models.py`  
  Token bundle, response envelope, and typed error payload models.
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/state.py`  
  Token state persistence and expiry-aware reads/writes.
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/auth.py`  
  Cached token reuse, refresh-token exchange, and auth resolution flow.
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/client.py`  
  Generic raw iFinD HTTP caller plus thin wrapper methods.
- `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/browser_login.py`  
  Headless Playwright login and token discovery logic.
- `tests/conftest.py`  
  Shared fixtures for temp state paths and fake sessions.
- `tests/test_cli.py`  
  Command routing tests for `auth-login`, `auth-set-tokens`, `api-call`, and wrappers.
- `tests/test_state.py`  
  Token persistence and expiry behavior.
- `tests/test_auth.py`  
  Cached token, refresh flow, and manual token injection behavior.
- `tests/test_client.py`  
  Raw API call, wrapper behavior, and iFinD error propagation.
- `tests/test_browser_login.py`  
  Token extraction and login flow behavior behind a fake Playwright adapter.

**Modify:**

- `docs/superpowers/specs/2026-04-06-tonghuashun-ifind-skill-design.md`  
  Only if implementation-driven clarifications become necessary. Do not change product meaning during implementation unless the user approves a spec change first.

## Notes Before Implementation

1. This repo currently contains only the approved spec and no runtime code.
2. Keep the skill raw-first. Do not add business-semantic financial abstractions.
3. Keep browser use limited to login/token capture. Do not add F10/page scraping.
4. Token logs must stay redacted from the first implementation step.
5. Use TDD strictly. Every new runtime unit starts with a failing test.

### Task 1: Bootstrap the Repository and CLI Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `tonghuashun-ifind/scripts/ifind_cli.py`
- Create: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/__init__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI import test**

```python
from pathlib import Path
import importlib.util


def test_ifind_cli_module_exists():
    cli_path = Path("tonghuashun-ifind/scripts/ifind_cli.py")
    assert cli_path.exists()
    spec = importlib.util.spec_from_file_location("ifind_cli", cli_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_ifind_cli_module_exists -v`  
Expected: FAIL because the CLI file does not exist yet.

- [ ] **Step 3: Add minimal repo scaffolding and CLI entrypoint**

```python
def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Also add the minimal `pyproject.toml`, `.gitignore`, and package marker so pytest/imports work.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py::test_ifind_cli_module_exists -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore README.md tonghuashun-ifind/scripts/ifind_cli.py tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/__init__.py tests/test_cli.py
git commit -m "chore: scaffold tonghuashun-ifind skill repo"
```

### Task 2: Add Token Models and Local State Persistence

**Files:**
- Create: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/models.py`
- Create: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write the failing state persistence test**

```python
from pathlib import Path

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_state.py::test_state_store_round_trips_token_bundle -v`  
Expected: FAIL because `models.py` and `state.py` do not exist yet.

- [ ] **Step 3: Implement the minimal token model and JSON state store**

```python
@dataclass
class TokenBundle:
    access_token: str
    refresh_token: str
    expires_at: str | None = None


class TokenStateStore:
    def save(self, bundle: TokenBundle) -> None: ...
    def load(self) -> TokenBundle | None: ...
```

Add an expiry helper here or in `models.py` so later auth code can ask whether the access token is stale.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_state.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/models.py tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/state.py tests/test_state.py
git commit -m "feat: add token state persistence"
```

### Task 3: Implement Cached Token Reuse and Refresh Exchange

**Files:**
- Create: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/auth.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: Write the failing cached-token test**

```python
from tonghuashun_ifind_skill.auth import AuthManager
from tonghuashun_ifind_skill.models import TokenBundle


def test_auth_manager_reuses_unexpired_access_token(tmp_path):
    manager = AuthManager.for_test(
        state_path=tmp_path / "tokens.json",
        refresh_exchange=lambda refresh_token: (_ for _ in ()).throw(AssertionError("should not refresh")),
        browser_login=lambda: (_ for _ in ()).throw(AssertionError("should not login")),
    )
    manager.state_store.save(TokenBundle("access-demo", "refresh-demo", "2099-01-01T00:00:00Z"))
    bundle, source = manager.resolve_tokens()
    assert bundle.access_token == "access-demo"
    assert source == "cache"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth.py::test_auth_manager_reuses_unexpired_access_token -v`  
Expected: FAIL because `AuthManager` does not exist yet.

- [ ] **Step 3: Implement minimal auth resolution and refresh exchange**

```python
class AuthManager:
    def resolve_tokens(self) -> tuple[TokenBundle, str]:
        bundle = self.state_store.load()
        if bundle and not bundle.is_expired():
            return bundle, "cache"
        if bundle and bundle.refresh_token:
            refreshed = self.refresh_exchange(bundle.refresh_token)
            self.state_store.save(refreshed)
            return refreshed, "refresh"
        raise RuntimeError("no valid tokens")
```

Add a second test in this task for refresh success, but keep browser login out of scope until Task 5.

- [ ] **Step 4: Run focused auth tests**

Run: `uv run pytest tests/test_auth.py -q`  
Expected: PASS for cache and refresh tests

- [ ] **Step 5: Commit**

```bash
git add tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/auth.py tests/test_auth.py
git commit -m "feat: add token refresh auth flow"
```

### Task 4: Build the Generic Raw API Client and Thin Wrappers

**Files:**
- Create: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/client.py`
- Modify: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/models.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write the failing raw-call test**

```python
from tonghuashun_ifind_skill.client import IFindClient


def test_api_call_posts_to_requested_endpoint(fake_session):
    client = IFindClient(
        base_url="https://quantapi.51ifind.com/api/v1",
        session=fake_session,
    )
    result = client.api_call(
        endpoint="/basic_data_service",
        payload={"codes": "300750.SZ"},
        access_token="access-demo",
        token_source="cache",
    )
    assert result["ok"] is True
    assert result["endpoint"] == "/basic_data_service"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_client.py::test_api_call_posts_to_requested_endpoint -v`  
Expected: FAIL because `IFindClient` does not exist yet.

- [ ] **Step 3: Implement generic client plus thin wrapper methods**

```python
class IFindClient:
    def api_call(self, endpoint: str, payload: dict[str, object], access_token: str, token_source: str) -> dict[str, object]:
        ...

    def basic_data(self, payload: dict[str, object], access_token: str, token_source: str) -> dict[str, object]:
        return self.api_call("/basic_data_service", payload, access_token, token_source)
```

Add wrapper methods for `smart_stock_picking`, `report_query`, and `date_sequence` only. Preserve iFinD `errorcode` / `errmsg` in the returned `error`.

- [ ] **Step 4: Run focused client tests**

Run: `uv run pytest tests/test_client.py -q`  
Expected: PASS for raw call, wrapper forwarding, and business-error propagation

- [ ] **Step 5: Commit**

```bash
git add tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/client.py tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/models.py tests/test_client.py
git commit -m "feat: add raw ifind api client"
```

### Task 5: Add Headless Playwright Login and Token Discovery

**Files:**
- Create: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/browser_login.py`
- Modify: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/auth.py`
- Test: `tests/test_browser_login.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: Write the failing browser-login test**

```python
from tonghuashun_ifind_skill.browser_login import extract_token_bundle


def test_extract_token_bundle_prefers_response_payload_over_storage():
    bundle = extract_token_bundle(
        response_candidates=[{"access_token": "access-a", "refresh_token": "refresh-a"}],
        request_header_candidates=[],
        storage_candidates=[{"access_token": "access-b", "refresh_token": "refresh-b"}],
        cookie_candidates=[],
    )
    assert bundle.access_token == "access-a"
    assert bundle.refresh_token == "refresh-a"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_browser_login.py::test_extract_token_bundle_prefers_response_payload_over_storage -v`  
Expected: FAIL because `browser_login.py` does not exist yet.

- [ ] **Step 3: Implement extraction helpers and auth fallback to browser login**

```python
def extract_token_bundle(... ) -> TokenBundle:
    ...


class BrowserLoginRunner:
    def login_and_capture(self, username: str, password: str) -> TokenBundle:
        ...
```

Keep Playwright behind a small adapter boundary so unit tests can use fakes. Then extend `AuthManager.resolve_tokens()` so refresh failure falls through to `browser_login`.

- [ ] **Step 4: Run browser and auth tests**

Run: `uv run pytest tests/test_browser_login.py tests/test_auth.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/browser_login.py tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/auth.py tests/test_browser_login.py tests/test_auth.py
git commit -m "feat: add playwright token capture flow"
```

### Task 6: Wire the CLI Commands and Response Envelopes

**Files:**
- Modify: `tonghuashun-ifind/scripts/ifind_cli.py`
- Modify: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/auth.py`
- Modify: `tonghuashun-ifind/scripts/runtime/tonghuashun_ifind_skill/client.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing command-routing test**

```python
from ifind_cli import main


def test_cli_basic_data_command_routes_to_client(monkeypatch, capsys):
    monkeypatch.setattr(
        "ifind_cli.run_command",
        lambda argv: {"ok": True, "endpoint": "/basic_data_service", "token_source": "manual", "data": {}, "error": None, "meta": {}},
    )
    exit_code = main(["basic-data", "--payload", '{"codes":"300750.SZ"}'])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"ok": true' in captured.out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_cli_basic_data_command_routes_to_client -v`  
Expected: FAIL because the CLI still only contains a placeholder.

- [ ] **Step 3: Implement CLI command parsing and shared command runner**

```python
def main(argv: list[str] | None = None) -> int:
    ...
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1
```

Support:

1. `auth-login`
2. `auth-set-tokens`
3. `api-call`
4. `basic-data`
5. `smart-pick`
6. `report-query`
7. `date-sequence`

- [ ] **Step 4: Run CLI tests**

Run: `uv run pytest tests/test_cli.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tonghuashun-ifind/scripts/ifind_cli.py tests/test_cli.py
git commit -m "feat: add raw-first skill cli commands"
```

### Task 7: Package the Actual OpenClaw Skill

**Files:**
- Create: `tonghuashun-ifind/SKILL.md`
- Create: `tonghuashun-ifind/agents/openai.yaml`
- Create: `tonghuashun-ifind/references/usage.md`
- Create: `scripts/install_skill.sh`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing packaging test**

```python
from pathlib import Path


def test_skill_package_contains_required_files():
    assert Path("tonghuashun-ifind/SKILL.md").exists()
    assert Path("tonghuashun-ifind/agents/openai.yaml").exists()
    assert Path("scripts/install_skill.sh").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_skill_package_contains_required_files -v`  
Expected: FAIL because the skill package files do not exist yet.

- [ ] **Step 3: Add skill metadata, usage reference, and install script**

`SKILL.md` must document:

1. `auth-login`
2. `auth-set-tokens`
3. `api-call`
4. thin wrappers
5. fallback rule: if automatic token capture fails, ask the customer for both tokens

`install_skill.sh` must copy the `tonghuashun-ifind/` directory into `~/.openclaw/workspace/skills/`.

- [ ] **Step 4: Run packaging test**

Run: `uv run pytest tests/test_cli.py::test_skill_package_contains_required_files -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tonghuashun-ifind/SKILL.md tonghuashun-ifind/agents/openai.yaml tonghuashun-ifind/references/usage.md scripts/install_skill.sh tests/test_cli.py
git commit -m "feat: package tonghuashun-ifind openclaw skill"
```

### Task 8: Add Validation Script and Repo-Level Documentation

**Files:**
- Modify: `README.md`
- Create: `scripts/validate_skill.sh`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing validation-script test**

```python
from pathlib import Path


def test_validation_script_exists():
    assert Path("scripts/validate_skill.sh").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_validation_script_exists -v`  
Expected: FAIL because the script does not exist yet.

- [ ] **Step 3: Add validation script and complete README**

`validate_skill.sh` should:

1. run `uv run pytest -q`,
2. run a minimal CLI smoke command,
3. print the expected install path for OpenClaw.

`README.md` should document:

1. how automatic login works,
2. how manual token injection works,
3. available commands,
4. local validation,
5. local OpenClaw installation.

- [ ] **Step 4: Run the script test and repo test suite**

Run: `uv run pytest -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md scripts/validate_skill.sh tests/test_cli.py
git commit -m "docs: add validation and usage guide"
```

## Release Checklist After Code Tasks

These are execution steps, not code-authoring tasks:

1. Run `scripts/validate_skill.sh`.
2. Run `scripts/install_skill.sh`.
3. Verify the skill appears under `~/.openclaw/workspace/skills/tonghuashun-ifind`.
4. Run one real `auth-login` attempt.
5. Run one real `api-call` against a permitted iFinD endpoint.
6. If automatic login fails, verify `auth-set-tokens` restores query capability.
7. Create the remote GitHub repository.
8. Push the repo.
9. Publish the skill to ClawHub/OpenClaw using the platform’s publish flow.

## Self-Review Checklist

Review the finished plan against the approved spec before implementation starts:

1. Raw API calling is still the primary contract.
2. Browser use is still limited to token capture.
3. No non-iFinD fallback provider work was added.
4. No heavy business-semantic abstraction was added.
5. All runtime units start with tests.
6. Every task has exact files, exact commands, and a commit step.
