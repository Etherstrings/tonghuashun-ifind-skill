from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace
from datetime import date
import json
import os
from typing import Any

from tonghuashun_ifind_skill.routing import ResolvedEntity
from tonghuashun_ifind_skill.routing import RoutePlan
from tonghuashun_ifind_skill.routing import build_capital_flow_plan
from tonghuashun_ifind_skill.routing import build_entity_profile_plan
from tonghuashun_ifind_skill.routing import build_fundamental_plan
from tonghuashun_ifind_skill.routing import build_generic_smart_query_plan
from tonghuashun_ifind_skill.routing import build_history_plan
from tonghuashun_ifind_skill.routing import build_leaderboard_plan
from tonghuashun_ifind_skill.routing import build_limit_up_plan
from tonghuashun_ifind_skill.routing import build_market_snapshot_plan
from tonghuashun_ifind_skill.routing import build_realtime_plan
from tonghuashun_ifind_skill.routing import build_trading_calendar_plan
from tonghuashun_ifind_skill.routing import normalize_symbol


_SUPPORTED_INTENTS = {
    "quote_realtime",
    "quote_history",
    "market_snapshot",
    "fundamental_basic",
    "limit_up_screen",
    "leaderboard_screen",
    "entity_profile",
    "capital_flow",
    "trading_calendar",
    "generic_smart_query",
    "manual_lookup",
}
_ENTITY_INTENTS = {
    "quote_realtime",
    "quote_history",
    "fundamental_basic",
    "entity_profile",
}
_TRUTHY = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LLMRoutingConfig:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 12.0
    min_confidence: float = 0.65

    @classmethod
    def from_env(cls) -> "LLMRoutingConfig | None":
        enabled_raw = os.environ.get("IFIND_ROUTE_LLM_ENABLED", "").strip().lower()
        api_key = (
            os.environ.get("IFIND_ROUTE_LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        ).strip()
        if enabled_raw not in _TRUTHY:
            return None
        if not api_key:
            return None

        model = os.environ.get("IFIND_ROUTE_LLM_MODEL", "gpt-4o-mini").strip()
        base_url = os.environ.get("IFIND_ROUTE_LLM_BASE_URL", cls.base_url).strip()
        timeout = _float_from_env("IFIND_ROUTE_LLM_TIMEOUT", cls.timeout)
        min_confidence = _float_from_env(
            "IFIND_ROUTE_LLM_MIN_CONFIDENCE",
            cls.min_confidence,
        )
        return cls(
            api_key=api_key,
            model=model,
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            min_confidence=min_confidence,
        )


def build_llm_route_plan(
    query: str,
    *,
    entity_lookup: Callable[[str], ResolvedEntity | None],
    today: date | None = None,
    session: Any | None = None,
    config: LLMRoutingConfig | None = None,
) -> RoutePlan | None:
    effective_config = config or LLMRoutingConfig.from_env()
    if effective_config is None:
        return None

    response_payload = _call_router_model(
        query=query,
        today=today or date.today(),
        session=session,
        config=effective_config,
    )
    if response_payload is None:
        return None
    return _route_json_to_plan(
        response_payload,
        query=query,
        today=today or date.today(),
        entity_lookup=entity_lookup,
        min_confidence=effective_config.min_confidence,
    )


def _call_router_model(
    *,
    query: str,
    today: date,
    session: Any | None,
    config: LLMRoutingConfig,
) -> dict[str, object] | None:
    client = session if session is not None else _default_session()
    payload = {
        "model": config.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 tonghuashun-ifind-skill skill 的自然语言路由器。"
                    "只返回 JSON 对象，不要返回解释。所有数据查询都必须走同花顺 iFinD，"
                    "不得规划腾讯、东方财富或其它公开源。"
                ),
            },
            {
                "role": "user",
                "content": _router_prompt(query=query, today=today),
            },
        ],
    }
    try:
        response = client.post(
            f"{config.base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout,
        )
        response.raise_for_status()
        raw = response.json()
    except Exception:
        return None

    content = _extract_chat_content(raw)
    if content is None:
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _router_prompt(*, query: str, today: date) -> str:
    return json.dumps(
        {
            "today": today.isoformat(),
            "query": query,
            "allowed_intents": sorted(_SUPPORTED_INTENTS),
            "output_schema": {
                "intent": "one allowed intent",
                "confidence": "0.0-1.0",
                "entity_text": "股票/指数名称，可为空",
                "symbol": "标准代码如 600519.SH，可为空",
                "entity_type": "stock 或 index，可为空",
                "start_date": "YYYY-MM-DD，仅 quote_history 需要",
                "end_date": "YYYY-MM-DD，仅 quote_history 需要",
                "searchstring": "传给 smart_stock_picking 的原始自然语言，可为空",
                "note": "manual_lookup 或低置信度原因，可为空",
            },
            "rules": [
                "行情、历史、大盘、基本面、涨停、榜单、画像、资金流都优先映射到 iFinD endpoint。",
                "公告、研报、龙虎榜、两融、北向、股东、持仓、分红、解禁、停复牌、概念板块、新股和交易日等 A 股常见问法，优先输出 generic_smart_query，并把用户原话放入 searchstring。",
                "休市、开不开盘、下一个交易日等交易日历问法，优先输出 trading_calendar。",
                "quote_history 没有日期时按最近 30 天。",
                "不要输出公开数据源、fallback_type、provider 或非 iFinD 字段。",
                "无法稳定判断时输出 manual_lookup。",
            ],
        },
        ensure_ascii=False,
    )


def _route_json_to_plan(
    payload: dict[str, object],
    *,
    query: str,
    today: date,
    entity_lookup: Callable[[str], ResolvedEntity | None],
    min_confidence: float,
) -> RoutePlan | None:
    intent = _text(payload.get("intent"))
    if intent not in _SUPPORTED_INTENTS:
        return None

    confidence = _float(payload.get("confidence"))
    if confidence is not None and confidence < min_confidence:
        return None

    if intent == "manual_lookup":
        return RoutePlan(
            intent="manual_lookup",
            endpoint=None,
            payload=None,
            entity=None,
            note=_text(payload.get("note"))
            or "大模型路由无法稳定映射该请求，请先查看 references/routing.md。",
        )

    searchstring = _text(payload.get("searchstring")) or query
    entity = None
    if intent in _ENTITY_INTENTS:
        entity = _entity_from_payload(payload)
        if entity is None:
            entity_hint = _text(payload.get("entity_text")) or query
            entity = entity_lookup(entity_hint)
        if entity is None:
            return None

    if intent == "quote_realtime":
        return _with_llm_note(build_realtime_plan(entity))
    if intent == "quote_history":
        return _with_llm_note(
            build_history_plan(
                entity,
                query=query,
                today=today,
                start_date=_text(payload.get("start_date")),
                end_date=_text(payload.get("end_date")),
            )
        )
    if intent == "fundamental_basic":
        return _with_llm_note(build_fundamental_plan(entity))
    if intent == "entity_profile":
        return _with_llm_note(build_entity_profile_plan(entity, searchstring))
    if intent == "market_snapshot":
        market_query = _text(payload.get("symbol")) or _text(payload.get("entity_text")) or query
        return _with_llm_note(build_market_snapshot_plan(market_query))
    if intent == "limit_up_screen":
        return _with_llm_note(build_limit_up_plan(searchstring))
    if intent == "leaderboard_screen":
        return _with_llm_note(build_leaderboard_plan(searchstring))
    if intent == "capital_flow":
        return _with_llm_note(build_capital_flow_plan(searchstring))
    if intent == "trading_calendar":
        return _with_llm_note(build_trading_calendar_plan(searchstring, today=today))
    if intent == "generic_smart_query":
        return _with_llm_note(build_generic_smart_query_plan(searchstring, entity=entity))
    return None


def _entity_from_payload(payload: dict[str, object]) -> ResolvedEntity | None:
    symbol = _text(payload.get("symbol"))
    if not symbol:
        return None
    normalized_symbol = normalize_symbol(symbol)
    entity_type = _text(payload.get("entity_type"))
    if entity_type not in {"stock", "index"}:
        entity_type = "index" if normalized_symbol in {
            "000001.SH",
            "399001.SZ",
            "399006.SZ",
            "000300.SH",
        } else "stock"
    return ResolvedEntity(
        raw=_text(payload.get("entity_text")) or normalized_symbol,
        symbol=normalized_symbol,
        name=_text(payload.get("entity_text")),
        entity_type=entity_type,
    )


def _with_llm_note(plan: RoutePlan) -> RoutePlan:
    note = "route_source=llm"
    if plan.note:
        note = f"{note}; {plan.note}"
    return replace(plan, note=note)


def _extract_chat_content(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) and content.strip() else None


def _default_session() -> Any:
    try:
        import requests
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("requests is required for LLM routing") from exc
    return requests.Session()


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _float_from_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    parsed = _float(value)
    return default if parsed is None else parsed
