from __future__ import annotations

from typing import Any
import json
import re

from tonghuashun_ifind_skill.routing import ResolvedEntity
from tonghuashun_ifind_skill.routing import RoutePlan
from tonghuashun_ifind_skill.routing import normalize_symbol


TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="
TENCENT_SEARCH_URL = "https://smartbox.gtimg.cn/s3/"
TENCENT_HISTORY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"


class TencentStockFallbackClient:
    def __init__(
        self,
        *,
        session: Any | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.session = session if session is not None else self._default_session()
        self.timeout = timeout

    def search_entity(self, text: str) -> ResolvedEntity | None:
        query = (text or "").strip()
        if not query:
            return None

        response = self.session.get(
            TENCENT_SEARCH_URL,
            params={"q": query, "t": "all"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = _extract_assignment_payload(_decode_bytes(response.content), "v_hint")
        if not payload:
            return None

        candidates = _parse_search_candidates(query, payload)
        return candidates[0] if candidates else None

    def fetch_realtime(self, symbols: list[str]) -> dict[str, object]:
        provider_symbols = [to_tencent_symbol(symbol) for symbol in symbols if symbol]
        response = self.session.get(
            f"{TENCENT_QUOTE_URL}{','.join(provider_symbols)}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        decoded = _decode_bytes(response.content)

        quotes: list[dict[str, object]] = []
        for segment in decoded.replace("\n", "").split(";"):
            item = segment.strip()
            if not item or "=" not in item:
                continue
            variable, raw_payload = item.split("=", 1)
            provider_symbol = variable.removeprefix("v_").strip()
            fields = raw_payload.strip().strip('"').split("~")
            if len(fields) < 34:
                continue
            code = fields[2].strip() if len(fields) > 2 else provider_symbol[2:]
            quotes.append(
                {
                    "symbol": normalize_symbol(f"{code}.{provider_symbol[:2]}"),
                    "provider_symbol": provider_symbol,
                    "name": fields[1].strip() if len(fields) > 1 else None,
                    "latest": _to_float(fields[3]),
                    "previous_close": _to_float(fields[4]),
                    "open": _to_float(fields[5]),
                    "volume": _to_float(fields[6]),
                    "market_time": fields[30].strip() if len(fields) > 30 else None,
                    "change": _to_float(fields[31]) if len(fields) > 31 else None,
                    "change_ratio": _to_float(fields[32]) if len(fields) > 32 else None,
                    "high": _to_float(fields[33]) if len(fields) > 33 else None,
                    "low": _to_float(fields[34]) if len(fields) > 34 else None,
                }
            )

        if not quotes:
            raise ValueError("tencent quote response did not contain usable quotes")

        return {
            "provider": {
                "name": "tencent_finance",
                "type": "public_http",
            },
            "quotes": quotes,
        }

    def fetch_history(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, object]:
        provider_symbol = to_tencent_symbol(symbol)
        var_name = "kline_dayqfq"
        response = self.session.get(
            TENCENT_HISTORY_URL,
            params={
                "_var": var_name,
                "param": f"{provider_symbol},day,{start_date},{end_date},640,qfqa",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = _parse_json_assignment(_decode_bytes(response.content), var_name)
        if payload.get("code") not in (0, "0", None):
            raise ValueError("tencent history response returned error")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("tencent history response missing data")
        symbol_payload = data.get(provider_symbol)
        if not isinstance(symbol_payload, dict):
            raise ValueError("tencent history response missing symbol data")
        candles_raw = symbol_payload.get("day")
        if not isinstance(candles_raw, list):
            raise ValueError("tencent history response missing day series")

        candles: list[dict[str, object]] = []
        for item in candles_raw:
            if not isinstance(item, list) or len(item) < 6:
                continue
            candles.append(
                {
                    "date": item[0],
                    "open": _to_float(item[1]),
                    "close": _to_float(item[2]),
                    "high": _to_float(item[3]),
                    "low": _to_float(item[4]),
                    "volume": _to_float(item[5]),
                }
            )

        if not candles:
            raise ValueError("tencent history response did not contain candles")

        return {
            "provider": {
                "name": "tencent_finance",
                "type": "public_http",
            },
            "symbol": symbol,
            "provider_symbol": provider_symbol,
            "candles": candles,
        }

    def execute_plan(self, plan: RoutePlan) -> dict[str, object]:
        if plan.intent in {"quote_realtime", "market_snapshot"}:
            payload = plan.payload or {}
            codes = payload.get("codes", "")
            symbols = [code.strip() for code in str(codes).split(",") if code.strip()]
            return self.fetch_realtime(symbols)
        if plan.intent == "quote_history":
            if plan.entity is None or not plan.payload:
                raise ValueError("history fallback requires resolved entity and payload")
            start_date = str(plan.payload.get("startdate", ""))
            end_date = str(plan.payload.get("enddate", ""))
            if not start_date or not end_date:
                raise ValueError("history fallback requires startdate and enddate")
            return self.fetch_history(
                symbol=plan.entity.symbol,
                start_date=start_date,
                end_date=end_date,
            )
        raise ValueError(f"unsupported fallback intent: {plan.intent}")

    @staticmethod
    def _default_session() -> Any:
        try:
            import requests
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("requests is required for Tencent fallback") from exc
        return requests.Session()


def to_tencent_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    if "." in normalized:
        code, market = normalized.split(".", 1)
        return f"{market.lower()}{code}"
    raw = normalized.lower()
    if raw.startswith(("sh", "sz", "bj")):
        return raw
    return raw


def _parse_search_candidates(query: str, payload: str) -> list[ResolvedEntity]:
    candidates: list[ResolvedEntity] = []
    for row in payload.split("^"):
        if not row.strip():
            continue
        fields = row.split("~")
        if len(fields) < 5:
            continue
        market, code, name, _, kind = fields[:5]
        if not market or not code:
            continue
        symbol = normalize_symbol(f"{code}.{market}")
        entity_type = "index" if kind == "ZS" else "stock"
        candidates.append(
            ResolvedEntity(
                raw=query,
                symbol=symbol,
                name=_decode_escaped_text(name) or None,
                entity_type=entity_type,
            )
        )
    return candidates


def _parse_json_assignment(text: str, variable_name: str) -> dict[str, object]:
    payload = _extract_assignment_payload(text, variable_name, allow_object=True)
    if not payload:
        raise ValueError("missing JSON assignment payload")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("JSON assignment payload must be an object")
    return parsed


def _extract_assignment_payload(
    text: str,
    variable_name: str,
    *,
    allow_object: bool = False,
) -> str | None:
    if allow_object:
        pattern = rf"{re.escape(variable_name)}=(\{{.*\}})"
    else:
        pattern = rf"{re.escape(variable_name)}=\"(.*)\""
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return None
    return match.group(1)


def _decode_bytes(content: bytes) -> str:
    for encoding in ("utf-8", "gbk", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _decode_escaped_text(value: str) -> str:
    if "\\u" not in value:
        return value
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value
