from pathlib import Path
from types import SimpleNamespace
import importlib.util
import subprocess
import sys

SCRIPT_DIR = Path("tonghuashun-ifind/scripts").resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ifind_cli import main
from ifind_cli import _build_auth_manager
from ifind_cli import run_command


def test_ifind_cli_module_exists():
    cli_path = Path("tonghuashun-ifind/scripts/ifind_cli.py")
    assert cli_path.exists()
    spec = importlib.util.spec_from_file_location("ifind_cli", cli_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_cli_basic_data_command_routes_to_client(monkeypatch, capsys):
    monkeypatch.setattr(
        "ifind_cli.run_command",
        lambda argv: {
            "ok": True,
            "endpoint": "/basic_data_service",
            "token_source": "manual",
            "data": {},
            "error": None,
            "meta": {},
        },
    )
    exit_code = main(["basic-data", "--payload", '{"codes":"300750.SZ"}'])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"ok": true' in captured.out.lower()


def test_auth_login_accepts_browser_executable(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class FakeAuthManager:
        def login_with_browser(self):
            return (
                SimpleNamespace(expires_at="2026-04-06T00:30:00Z"),
                "playwright",
            )

    def fake_build_auth_manager(**kwargs):
        captured.update(kwargs)
        return FakeAuthManager()

    monkeypatch.setattr("ifind_cli._build_auth_manager", fake_build_auth_manager)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "auth-login",
            "--username",
            "alice",
            "--password",
            "secret",
            "--browser-executable",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    )

    assert result["ok"] is True
    assert (
        captured["browser_executable"]
        == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )


def test_build_auth_manager_uses_base_url_for_refresh(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_exchange_refresh_token(refresh_token: str, *, base_url: str, **kwargs):
        captured["refresh_token"] = refresh_token
        captured["base_url"] = base_url
        return SimpleNamespace(
            access_token="access-refreshed",
            refresh_token=refresh_token,
            expires_at="2099-01-01T00:00:00Z",
        )

    monkeypatch.setattr(
        "tonghuashun_ifind_skill.auth.exchange_refresh_token",
        fake_exchange_refresh_token,
    )

    manager = _build_auth_manager(
        state_path=tmp_path / "token_state.json",
        username=None,
        password=None,
        login_url="https://example.com/login",
        username_selector='input[name="username"]',
        password_selector='input[name="password"]',
        submit_selector='button[type="submit"]',
        browser_executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        base_url="https://example.com/api/v1",
    )

    bundle = manager.refresh_exchange("refresh-demo")

    assert captured["refresh_token"] == "refresh-demo"
    assert captured["base_url"] == "https://example.com/api/v1"
    assert bundle.access_token == "access-refreshed"


def test_skill_package_contains_required_files():
    assert Path("tonghuashun-ifind/SKILL.md").exists()
    assert Path("tonghuashun-ifind/agents/openai.yaml").exists()
    assert Path("scripts/install_skill.sh").exists()


def test_validation_script_exists():
    assert Path("scripts/validate_skill.sh").exists()


def test_cli_auth_set_tokens_runs_under_system_python3(tmp_path):
    result = subprocess.run(
        [
            "/usr/bin/python3",
            "tonghuashun-ifind/scripts/ifind_cli.py",
            "--state-path",
            str(tmp_path / "token_state.json"),
            "auth-set-tokens",
            "--access-token",
            "demo-access",
            "--refresh-token",
            "demo-refresh",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
