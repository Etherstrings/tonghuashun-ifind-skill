from pathlib import Path
from types import SimpleNamespace
import importlib.util
import subprocess
import sys

SCRIPT_DIR = Path("tonghuashun-ifind-skill/scripts").resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ifind_cli import main
from ifind_cli import _build_auth_manager
from ifind_cli import run_command
from tonghuashun_ifind_skill.models import TokenBundle


def test_ifind_cli_module_exists():
    cli_path = Path("tonghuashun-ifind-skill/scripts/ifind_cli.py")
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


def test_auth_set_refresh_token_exchanges_and_stores_token(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_exchange_refresh_token(refresh_token: str, *, base_url: str, **kwargs):
        captured["refresh_token"] = refresh_token
        captured["base_url"] = base_url
        return TokenBundle(
            access_token="access-new",
            refresh_token=refresh_token,
            expires_at="2099-01-01T00:00:00Z",
        )

    monkeypatch.setattr(
        "tonghuashun_ifind_skill.auth.exchange_refresh_token",
        fake_exchange_refresh_token,
    )

    state_path = tmp_path / "token_state.json"
    result = run_command(
        [
            "--state-path",
            str(state_path),
            "auth-set-refresh-token",
            "--refresh-token",
            "refresh-demo",
            "--base-url",
            "https://example.com/api/v1",
        ]
    )

    assert result["ok"] is True
    assert result["endpoint"] == "/auth/set-refresh-token"
    assert result["token_source"] == "refresh"
    assert captured["refresh_token"] == "refresh-demo"
    assert captured["base_url"] == "https://example.com/api/v1"
    assert "access-new" in state_path.read_text(encoding="utf-8")


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


def test_endpoint_list_returns_catalog() -> None:
    result = run_command(["endpoint-list"])

    assert result["ok"] is True
    assert result["endpoint"] == "/endpoint_catalog"
    endpoints = result["data"]["endpoints"]
    assert any(item["name"] == "basic_data" for item in endpoints)
    assert any(item["name"] == "history_quote" for item in endpoints)
    real_time_quote = next(item for item in endpoints if item["name"] == "real_time_quote")
    assert "indicators" in real_time_quote["example_payload"]


def test_endpoint_call_routes_named_endpoint(monkeypatch, tmp_path):
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

        def call_named_endpoint(self, name, payload, access_token, token_source):
            assert name == "history_quote"
            assert payload["codes"] == "600004.SH"
            assert access_token == "access-demo"
            assert token_source == "cache"
            return {
                "ok": True,
                "endpoint": "/cmd_history_quotation",
                "token_source": token_source,
                "data": {"rows": [{"open": 8.88, "close": 8.89}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "endpoint-call",
            "--name",
            "history_quote",
            "--payload",
            '{"codes":"600004.SH","startdate":"2026-04-21","enddate":"2026-04-21"}',
        ]
    )

    assert result["ok"] is True
    assert result["endpoint"] == "/cmd_history_quotation"
    assert result["data"]["rows"][0]["open"] == 8.88


def test_endpoint_call_rejects_unknown_name(tmp_path):
    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "endpoint-call",
            "--name",
            "not_exist",
            "--payload",
            "{}",
        ]
    )

    assert result["ok"] is False
    assert result["endpoint"] == "/endpoint_catalog"
    assert result["error"]["type"] == "invalid_request"
    assert "unknown endpoint name" in result["error"]["message"]


def test_quote_realtime_requires_ifind_auth_when_auth_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "quote-realtime",
            "--symbol",
            "600519",
        ]
    )

    assert result["ok"] is False
    assert result["token_source"] == "cli"
    assert result["error"]["type"] == "auth_required"
    assert "iFinD authentication is required" in result["error"]["message"]
    assert "AccountDetails" in result["error"]["message"]
    assert "refresh_token" in result["error"]["message"]
    assert "auth-set-refresh-token" in result["error"]["message"]
    assert "username or password" in result["error"]["message"]


def test_quote_history_requires_ifind_auth_when_auth_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "quote-history",
            "--symbol",
            "600004",
            "--start-date",
            "2026-04-21",
            "--end-date",
            "2026-04-21",
        ]
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "auth_required"


def test_smart_query_requires_ifind_auth_before_entity_lookup(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "看看贵州茅台现在股价",
        ]
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "auth_required"


def test_smart_query_with_numeric_stock_code_still_requires_ifind_auth(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "600004 2026-04-21 开盘价 收盘价",
        ]
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "auth_required"


def test_smart_query_uses_ifind_entity_lookup_without_public_source(
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
            self.calls: list[dict[str, object]] = []

        def smart_stock_picking(self, payload, access_token, token_source):
            self.calls.append({"method": "smart_stock_picking", "payload": payload})
            return {
                "ok": True,
                "endpoint": "/smart_stock_picking",
                "token_source": token_source,
                "data": {
                    "tables": [
                        {
                            "table": {
                                "股票代码": ["600519.SH"],
                                "股票简称": ["贵州茅台"],
                            }
                        }
                    ]
                },
                "error": None,
                "meta": {},
            }

        def api_call(self, endpoint, payload, access_token, token_source):
            assert endpoint == "/real_time_quotation"
            assert payload["codes"] == "600519.SH"
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"latest": [1462.84]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

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
    assert result["token_source"] == "cache"
    assert result["data"]["entity"]["symbol"] == "600519.SH"
    assert result["data"]["response"] == {"tables": [{"table": {"latest": [1462.84]}}]}


def test_smart_query_resolves_chinese_stock_name_to_code_via_ifind_lookup(
    monkeypatch,
    tmp_path,
):
    calls: list[dict[str, object]] = []

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

        def smart_stock_picking(self, payload, access_token, token_source):
            calls.append({"method": "smart_stock_picking", "payload": payload})
            assert payload == {
                "searchstring": "贵州茅台 股票代码 股票简称",
                "searchtype": "stock",
            }
            return {
                "ok": True,
                "endpoint": "/smart_stock_picking",
                "token_source": token_source,
                "data": {
                    "tables": [
                        {
                            "table": {
                                "股票代码": ["600519.SH"],
                                "股票简称": ["贵州茅台"],
                            }
                        }
                    ]
                },
                "error": None,
                "meta": {},
            }

        def api_call(self, endpoint, payload, access_token, token_source):
            calls.append({"method": "api_call", "endpoint": endpoint, "payload": payload})
            assert endpoint == "/real_time_quotation"
            assert payload["codes"] == "600519.SH"
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"latest": [1462.84]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "请问贵州茅台最近股价怎么样",
        ]
    )

    assert result["ok"] is True
    assert result["data"]["entity"]["symbol"] == "600519.SH"
    assert result["data"]["request"]["payload"]["codes"] == "600519.SH"
    assert [call["method"] for call in calls] == ["smart_stock_picking", "api_call"]


def test_smart_query_casual_alias_overrides_wrong_ifind_lookup(
    monkeypatch,
    tmp_path,
):
    calls: list[dict[str, object]] = []

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

        def smart_stock_picking(self, payload, access_token, token_source):
            calls.append({"method": "smart_stock_picking", "payload": payload})
            return {
                "ok": True,
                "endpoint": "/smart_stock_picking",
                "token_source": token_source,
                "data": {
                    "tables": [
                        {
                            "table": {
                                "股票代码": ["000008.SZ"],
                                "股票简称": ["神州高铁"],
                            }
                        }
                    ]
                },
                "error": None,
                "meta": {},
            }

        def api_call(self, endpoint, payload, access_token, token_source):
            calls.append({"method": "api_call", "endpoint": endpoint, "payload": payload})
            assert endpoint == "/real_time_quotation"
            assert payload["codes"] == "300750.SZ"
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"latest": [444.9]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "宁王今天咋样",
        ]
    )

    assert result["ok"] is True
    assert result["data"]["intent"] == "quote_realtime"
    assert result["data"]["entity"]["symbol"] == "300750.SZ"
    assert result["data"]["entity"]["name"] == "宁德时代"
    assert [call["method"] for call in calls] == ["smart_stock_picking", "api_call"]


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

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

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


def test_limit_up_query_requires_ifind_auth_when_auth_fails(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise RuntimeError("ifind unavailable")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "今天的A股涨停数据",
        ]
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "auth_required"


def test_limit_up_query_returns_ifind_api_error_without_alternate_source(
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

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "今天的A股涨停数据",
        ]
    )

    assert result["ok"] is False
    assert result["token_source"] == "cache"
    assert result["data"]["intent"] == "limit_up_screen"
    assert "provider" not in result["data"]


def test_leaderboard_query_sends_raw_ifind_searchstring_without_public_fields(
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
            assert endpoint == "/smart_stock_picking"
            assert payload == {
                "searchstring": "A股成交额榜前十",
                "searchtype": "stock",
            }
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"结果": ["ok"]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

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
    assert result["data"]["intent"] == "leaderboard_screen"
    assert result["data"]["request"]["payload"] == {
        "searchstring": "A股成交额榜前十",
        "searchtype": "stock",
    }


def test_volume_ratio_leaderboard_keeps_limit_in_ifind_searchstring_only(
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
            assert payload == {
                "searchstring": "量比榜前十",
                "searchtype": "stock",
            }
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"结果": ["ok"]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "量比榜前十",
        ]
    )

    assert result["ok"] is True
    assert result["data"]["intent"] == "leaderboard_screen"
    assert result["data"]["request"]["payload"] == {
        "searchstring": "量比榜前十",
        "searchtype": "stock",
    }


def test_complex_natural_language_query_falls_through_to_ifind_smart_pick(
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

        def smart_stock_picking(self, payload, access_token, token_source):
            return {
                "ok": False,
                "endpoint": "/smart_stock_picking",
                "token_source": token_source,
                "data": None,
                "error": {"type": "api_failed", "message": "no entity lookup"},
                "meta": {},
            }

        def api_call(self, endpoint, payload, access_token, token_source):
            assert endpoint == "/smart_stock_picking"
            assert payload == {
                "searchstring": "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票",
                "searchtype": "stock",
            }
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"结果": ["ok"]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票",
        ]
    )

    assert result["ok"] is True
    assert result["data"]["intent"] == "generic_smart_query"
    assert result["data"]["request"]["payload"]["searchstring"].startswith("筛一下新能源车")


def test_smart_query_blank_or_punctuation_query_stops_before_auth(
    monkeypatch,
    tmp_path,
):
    class FakeAuthManager:
        def resolve_tokens(self):
            raise AssertionError("blank query should not require iFinD auth")

    monkeypatch.setattr("ifind_cli._build_auth_manager", lambda **kwargs: FakeAuthManager())

    result = run_command(
        [
            "--state-path",
            str(tmp_path / "token_state.json"),
            "smart-query",
            "--query",
            "？？？",
        ]
    )

    assert result["ok"] is False
    assert result["endpoint"] == "/manual_lookup"
    assert result["error"]["type"] == "manual_api_lookup_required"
    assert "空白或纯标点" in result["error"]["message"]


def test_auth_refresh_then_extreme_smart_queries_run_end_to_end(
    monkeypatch,
    tmp_path,
):
    monkeypatch.delenv("IFIND_ROUTE_LLM_ENABLED", raising=False)
    calls: list[dict[str, object]] = []
    entity_symbols = {
        "贵州茅台": "600519.SH",
        "药明康德": "603259.SH",
    }

    def fake_exchange_refresh_token(refresh_token: str, *, base_url: str, **kwargs):
        calls.append(
            {
                "method": "exchange_refresh_token",
                "refresh_token": refresh_token,
                "base_url": base_url,
            }
        )
        return TokenBundle(
            access_token="access-from-refresh",
            refresh_token=refresh_token,
            expires_at="2099-01-01T00:00:00Z",
        )

    class FakeClient:
        def __init__(self, *, base_url, session=None, timeout=30.0, now=None):
            self.base_url = base_url

        def smart_stock_picking(self, payload, access_token, token_source):
            calls.append(
                {
                    "method": "smart_stock_picking",
                    "payload": payload,
                    "access_token": access_token,
                    "token_source": token_source,
                }
            )
            searchstring = payload["searchstring"]
            entity_name = searchstring.removesuffix(" 股票代码 股票简称")
            symbol = entity_symbols[entity_name]
            return {
                "ok": True,
                "endpoint": "/smart_stock_picking",
                "token_source": token_source,
                "data": {
                    "tables": [
                        {
                            "table": {
                                "股票代码": [symbol],
                                "股票简称": [entity_name],
                            }
                        }
                    ]
                },
                "error": None,
                "meta": {},
            }

        def api_call(self, endpoint, payload, access_token, token_source):
            calls.append(
                {
                    "method": "api_call",
                    "endpoint": endpoint,
                    "payload": payload,
                    "access_token": access_token,
                    "token_source": token_source,
                }
            )
            return {
                "ok": True,
                "endpoint": endpoint,
                "token_source": token_source,
                "data": {"tables": [{"table": {"结果": ["ok"]}}]},
                "error": None,
                "meta": {},
            }

    monkeypatch.setattr(
        "tonghuashun_ifind_skill.auth.exchange_refresh_token",
        fake_exchange_refresh_token,
    )
    monkeypatch.setattr("tonghuashun_ifind_skill.client.IFindClient", FakeClient)

    state_path = tmp_path / "token_state.json"
    auth_result = run_command(
        [
            "--state-path",
            str(state_path),
            "auth-set-refresh-token",
            "--refresh-token",
            "refresh-demo",
            "--base-url",
            "https://example.com/api/v1",
        ]
    )
    assert auth_result["ok"] is True

    realtime_result = run_command(
        [
            "--state-path",
            str(state_path),
            "smart-query",
            "--query",
            "请问：贵州茅台，最新价是多少？",
        ]
    )
    index_result = run_command(
        [
            "--state-path",
            str(state_path),
            "smart-query",
            "--query",
            "000300sh行情",
        ]
    )
    holding_result = run_command(
        [
            "--state-path",
            str(state_path),
            "smart-query",
            "--query",
            "药明康德十大流通股东情况",
        ]
    )
    limit_up_result = run_command(
        [
            "--state-path",
            str(state_path),
            "smart-query",
            "--query",
            "今天 A 股 涨停板 都有哪些",
        ]
    )

    assert realtime_result["ok"] is True
    assert realtime_result["data"]["intent"] == "quote_realtime"
    assert realtime_result["data"]["entity"]["symbol"] == "600519.SH"
    assert realtime_result["data"]["request"]["payload"]["codes"] == "600519.SH"

    assert index_result["ok"] is True
    assert index_result["data"]["intent"] == "market_snapshot"
    assert index_result["data"]["request"]["payload"]["codes"] == "000300.SH"

    assert holding_result["ok"] is True
    assert holding_result["data"]["intent"] == "generic_smart_query"
    assert holding_result["data"]["entity"]["symbol"] == "603259.SH"
    assert holding_result["data"]["request"]["payload"] == {
        "searchstring": "药明康德十大流通股东情况",
        "searchtype": "stock",
    }

    assert limit_up_result["ok"] is True
    assert limit_up_result["data"]["intent"] == "limit_up_screen"
    assert limit_up_result["data"]["request"]["payload"] == {
        "searchstring": "今天 A 股 涨停板 都有哪些",
        "searchtype": "stock",
    }

    api_calls = [call for call in calls if call["method"] == "api_call"]
    assert [call["endpoint"] for call in api_calls] == [
        "/real_time_quotation",
        "/real_time_quotation",
        "/smart_stock_picking",
        "/smart_stock_picking",
    ]
    assert all(call["access_token"] == "access-from-refresh" for call in api_calls)
    assert all(call["token_source"] == "cache" for call in api_calls)


def test_skill_package_contains_required_files():
    assert Path("tonghuashun-ifind-skill/SKILL.md").exists()
    assert Path("tonghuashun-ifind-skill/agents/openai.yaml").exists()
    assert Path("scripts/install_skill.sh").exists()


def test_validation_script_exists():
    assert Path("scripts/validate_skill.sh").exists()


def test_cli_auth_set_tokens_runs_under_system_python3(tmp_path):
    result = subprocess.run(
        [
            "/usr/bin/python3",
            "tonghuashun-ifind-skill/scripts/ifind_cli.py",
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
