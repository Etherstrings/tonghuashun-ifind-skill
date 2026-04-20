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


def test_cli_smart_query_routes_to_routed_handler(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_handle_routed_query_command(args, state_path):
        captured["command"] = args.command
        captured["query"] = args.query
        captured["state_path"] = state_path
        return {
            "ok": True,
            "endpoint": "/real_time_quotation",
            "token_source": "manual",
            "data": {"intent": "market_snapshot"},
            "error": None,
            "meta": {},
        }

    monkeypatch.setattr(
        "ifind_cli._handle_routed_query_command",
        fake_handle_routed_query_command,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "看一下大盘",
        ]
    )

    assert result["ok"] is True
    assert captured["command"] == "smart-query"
    assert captured["query"] == "看一下大盘"
    assert captured["state_path"] == tmp_path / "token_state.json"


def test_quote_realtime_falls_back_to_tencent_when_ifind_auth_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    class FakeTencentFallbackClient:
        def __init__(self, **kwargs):
            return None

        def execute_plan(self, plan):
            return {
                "provider": {"name": "tencent_finance"},
                "quotes": [{"symbol": "600519.SH", "latest": 1462.84}],
                "fallback_reason": "ifind unavailable",
                "fallback_for": plan.intent,
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.fallback.TencentStockFallbackClient",
        FakeTencentFallbackClient,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "quote-realtime",
            "--symbol",
            "600519",
        ]
    )

    assert result["ok"] is True
    assert result["token_source"] == "fallback:tencent"
    assert result["data"]["provider"]["name"] == "tencent_finance"
    assert result["data"]["entity"]["symbol"] == "600519.SH"


def test_smart_query_uses_tencent_search_when_ifind_lookup_unavailable(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    class FakeTencentFallbackClient:
        def __init__(self, **kwargs):
            return None

        def search_entity(self, text):
            from tonghuashun_ifind_skill.routing import ResolvedEntity

            assert text == "贵州茅台"
            return ResolvedEntity(
                raw="贵州茅台",
                symbol="600519.SH",
                name="贵州茅台",
                entity_type="stock",
            )

        def execute_plan(self, plan):
            return {
                "provider": {"name": "tencent_finance"},
                "quotes": [{"symbol": "600519.SH", "latest": 1462.84}],
                "fallback_reason": "ifind unavailable",
                "fallback_for": plan.intent,
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.fallback.TencentStockFallbackClient",
        FakeTencentFallbackClient,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "看看贵州茅台现在股价",
        ]
    )

    assert result["ok"] is True
    assert result["token_source"] == "fallback:tencent"
    assert result["data"]["entity"]["symbol"] == "600519.SH"


def test_smart_query_limit_up_uses_smart_stock_picking_route(monkeypatch, tmp_path):
    class FakeAuthManager:
        def resolve_tokens(self):
            return (
                SimpleNamespace(
                    access_token="access-demo",
                    refresh_token="refresh-demo",
                    expires_at="2099-01-01T00:00:00Z",
                ),
                "cache",
            )

    class FakeClient:
        def __init__(self, *, base_url, session=None, timeout=30.0, now=None):
            self.base_url = base_url

        def api_call(self, endpoint, payload, access_token, token_source):
            assert endpoint == "/smart_stock_picking"
            assert payload == {
                "searchstring": "今天的A股涨停数据",
                "searchtype": "stock",
            }
            assert access_token == "access-demo"
            assert token_source == "cache"
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"结果": ["ok"]}}]},
                "error": None,
                "meta": {},
            }

    class FakeTencentFallbackClient:
        def __init__(self, **kwargs):
            return None

        def search_entity(self, text):
            raise AssertionError(f"entity lookup should not run for limit-up queries: {text}")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.fallback.TencentStockFallbackClient",
        FakeTencentFallbackClient,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "今天的A股涨停数据",
        ]
    )

    assert result["ok"] is True
    assert result["endpoint"] == "/smart_stock_picking"
    assert result["data"]["intent"] == "limit_up_screen"
    assert result["data"]["entity"] is None
    assert result["data"]["request"]["payload"] == {
        "searchstring": "今天的A股涨停数据",
        "searchtype": "stock",
    }


def test_limit_up_query_falls_back_to_public_source_when_ifind_auth_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    class FakeTencentFallbackClient:
        def __init__(self, **kwargs):
            return None

        def execute_plan(self, plan):
            assert plan.intent == "limit_up_screen"
            return {
                "provider": {"name": "eastmoney", "type": "public_http"},
                "trade_date": "2026-04-20",
                "limit_up_stocks": [{"symbol": "002843.SZ", "name": "泰嘉股份"}],
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.fallback.TencentStockFallbackClient",
        FakeTencentFallbackClient,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "今天的A股涨停数据",
        ]
    )

    assert result["ok"] is True
    assert result["token_source"] == "fallback:eastmoney"
    assert result["data"]["intent"] == "limit_up_screen"
    assert result["data"]["provider"]["name"] == "eastmoney"


def test_limit_up_query_falls_back_to_public_source_when_ifind_api_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            return (
                SimpleNamespace(
                    access_token="access-demo",
                    refresh_token="refresh-demo",
                    expires_at="2099-01-01T00:00:00Z",
                ),
                "cache",
            )

    class FakeClient:
        def __init__(self, *, base_url, session=None, timeout=30.0, now=None):
            self.base_url = base_url

        def api_call(self, endpoint, payload, access_token, token_source):
            return {
                "ok": False,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": None,
                "error": {"type": "api_failed", "message": "token invalid"},
                "meta": {},
            }

    class FakeTencentFallbackClient:
        def __init__(self, **kwargs):
            return None

        def execute_plan(self, plan):
            assert plan.intent == "limit_up_screen"
            return {
                "provider": {"name": "eastmoney", "type": "public_http"},
                "trade_date": "2026-04-20",
                "limit_up_stocks": [{"symbol": "002843.SZ", "name": "泰嘉股份"}],
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.fallback.TencentStockFallbackClient",
        FakeTencentFallbackClient,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "今天的A股涨停数据",
        ]
    )

    assert result["ok"] is True
    assert result["token_source"] == "fallback:eastmoney"
    assert result["data"]["provider"]["name"] == "eastmoney"


def test_leaderboard_query_falls_back_to_public_source_when_ifind_auth_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    class FakeTencentFallbackClient:
        def __init__(self, **kwargs):
            return None

        def execute_plan(self, plan):
            assert plan.intent == "leaderboard_screen"
            assert plan.payload["fallback_type"] == "turnover"
            assert plan.payload["limit"] == 10
            return {
                "provider": {"name": "eastmoney", "type": "public_http"},
                "leaderboard_type": "turnover",
                "items": [{"symbol": "600519.SH", "name": "贵州茅台"}],
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr(
        "tonghuashun_ifind_skill.fallback.TencentStockFallbackClient",
        FakeTencentFallbackClient,
    )

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "A股成交额榜前十",
        ]
    )

    assert result["ok"] is True
    assert result["token_source"] == "fallback:eastmoney"
    assert result["data"]["intent"] == "leaderboard_screen"
    assert result["data"]["provider"]["name"] == "eastmoney"


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
