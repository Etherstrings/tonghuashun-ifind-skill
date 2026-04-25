from __future__ import annotations

from datetime import date
import json as json_module

from tonghuashun_ifind_skill.llm_routing import LLMRoutingConfig
from tonghuashun_ifind_skill.llm_routing import build_llm_route_plan
from tonghuashun_ifind_skill.routing import ResolvedEntity


def test_llm_routing_config_from_env_requires_explicit_enable(monkeypatch):
    monkeypatch.delenv("IFIND_ROUTE_LLM_ENABLED", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "existing-openai-key")

    assert LLMRoutingConfig.from_env() is None


def test_llm_routing_config_from_env_uses_key_when_enabled(monkeypatch):
    monkeypatch.setenv("IFIND_ROUTE_LLM_ENABLED", "1")
    monkeypatch.setenv("IFIND_ROUTE_LLM_API_KEY", "ifind-router-key")
    monkeypatch.setenv("IFIND_ROUTE_LLM_MODEL", "router-model")

    config = LLMRoutingConfig.from_env()

    assert config is not None
    assert config.api_key == "ifind-router-key"
    assert config.model == "router-model"


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class FakeSession:
    def __init__(self, route_payload: dict[str, object]) -> None:
        self.route_payload = route_payload
        self.requests: list[dict[str, object]] = []

    def post(
        self,
        url: str,
        *,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: float,
    ) -> FakeResponse:
        self.requests.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                self.route_payload,
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )


def test_llm_route_plan_builds_history_plan_from_structured_response():
    session = FakeSession(
        {
            "intent": "quote_history",
            "confidence": 0.91,
            "entity_text": "贵州茅台",
            "symbol": "600519.SH",
            "entity_type": "stock",
            "start_date": "2026-04-01",
            "end_date": "2026-04-25",
        }
    )
    config = LLMRoutingConfig(api_key="test-key", model="router-model")

    plan = build_llm_route_plan(
        "看一下贵州茅台四月以来走势",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 25),
        session=session,
        config=config,
    )

    assert plan is not None
    assert plan.intent == "quote_history"
    assert plan.endpoint == "/cmd_history_quotation"
    assert plan.payload["codes"] == "600519.SH"
    assert plan.payload["startdate"] == "2026-04-01"
    assert plan.payload["enddate"] == "2026-04-25"
    assert plan.note == "route_source=llm"
    assert session.requests[0]["url"] == "https://api.openai.com/v1/chat/completions"


def test_llm_route_plan_uses_ifind_entity_lookup_when_symbol_missing():
    session = FakeSession(
        {
            "intent": "quote_realtime",
            "confidence": 0.88,
            "entity_text": "宁德时代",
        }
    )
    config = LLMRoutingConfig(api_key="test-key", model="router-model")

    plan = build_llm_route_plan(
        "宁德时代现在股价",
        entity_lookup=lambda text: ResolvedEntity(
            raw=text,
            symbol="300750.SZ",
            name="宁德时代",
            entity_type="stock",
        ),
        today=date(2026, 4, 25),
        session=session,
        config=config,
    )

    assert plan is not None
    assert plan.intent == "quote_realtime"
    assert plan.payload["codes"] == "300750.SZ"


def test_llm_route_plan_ignores_low_confidence_response():
    session = FakeSession(
        {
            "intent": "quote_realtime",
            "confidence": 0.2,
            "symbol": "600519.SH",
        }
    )
    config = LLMRoutingConfig(api_key="test-key", model="router-model")

    plan = build_llm_route_plan(
        "可能查一下这个",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 25),
        session=session,
        config=config,
    )

    assert plan is None


def test_llm_route_plan_supports_generic_ifind_smart_query():
    session = FakeSession(
        {
            "intent": "generic_smart_query",
            "confidence": 0.86,
            "searchstring": "筛一下新能源车产业链里市盈率低于30的股票",
        }
    )
    config = LLMRoutingConfig(api_key="test-key", model="router-model")

    plan = build_llm_route_plan(
        "帮我找新能源车里面估值别太高的",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 25),
        session=session,
        config=config,
    )

    assert plan is not None
    assert plan.intent == "generic_smart_query"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.payload == {
        "searchstring": "筛一下新能源车产业链里市盈率低于30的股票",
        "searchtype": "stock",
    }


def test_llm_route_plan_supports_trading_calendar():
    session = FakeSession(
        {
            "intent": "trading_calendar",
            "confidence": 0.9,
            "searchstring": "下个交易日是哪天",
        }
    )
    config = LLMRoutingConfig(api_key="test-key", model="router-model")

    plan = build_llm_route_plan(
        "下个交易日是哪天",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 26),
        session=session,
        config=config,
    )

    assert plan is not None
    assert plan.intent == "trading_calendar"
    assert plan.endpoint == "/date_sequence"
    assert plan.payload["codes"] == "000001.SH"
    assert plan.payload["startdate"] == "2026-04-27"
    assert plan.note.startswith("route_source=llm")
