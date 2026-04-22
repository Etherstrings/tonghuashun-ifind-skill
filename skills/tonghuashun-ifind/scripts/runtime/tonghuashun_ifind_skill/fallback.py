from __future__ import annotations

from datetime import date
from typing import Any
import json
import re

from tonghuashun_ifind_skill.routing import ResolvedEntity
from tonghuashun_ifind_skill.routing import RoutePlan
from tonghuashun_ifind_skill.routing import normalize_symbol


TENCENT_QUOTE_URL = "https://qt.gtimg.cn/q="
TENCENT_SEARCH_URL = "https://smartbox.gtimg.cn/s3/"
TENCENT_HISTORY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
EASTMONEY_LIMIT_UP_URL = "https://push2ex.eastmoney.com/getTopicZTPool"
EASTMONEY_LEADERBOARD_URL = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_LIMIT_UP_UT = "7eea3edcaed734bea9cbfc24409ed989"
EASTMONEY_A_STOCK_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"

LEADERBOARD_PARAM_MAP: dict[str, dict[str, object]] = {
    "gainers": {"fid": "f3", "po": 1},
    "losers": {"fid": "f3", "po": 0},
    "turnover": {"fid": "f6", "po": 1},
    "turnover_ratio": {"fid": "f8", "po": 1},
    "amplitude": {"fid": "f7", "po": 1},
    "volume_ratio": {"fid": "f10", "po": 1},
}


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

    def fetch_limit_up_pool(
        self,
        *,
        trade_date: date,
    ) -> dict[str, object]:
        response = self.session.get(
            EASTMONEY_LIMIT_UP_URL,
            params={
                "ut": EASTMONEY_LIMIT_UP_UT,
                "dpt": "wz.ztzt",
                "Pageindex": 0,
                "pagesize": 10000,
                "sort": "fbt:asc",
                "date": trade_date.strftime("%Y%m%d"),
                "_": "",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("eastmoney limit-up response must be a JSON object")
        if payload.get("rc") not in (0, "0", None):
            raise ValueError("eastmoney limit-up response returned error")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("eastmoney limit-up response missing data")
        pool = data.get("pool")
        if not isinstance(pool, list):
            raise ValueError("eastmoney limit-up response missing pool")

        records = [
            _parse_eastmoney_limit_up_row(item)
            for item in pool
            if isinstance(item, dict)
        ]
        if not records:
            raise ValueError("eastmoney limit-up response did not contain records")

        return {
            "provider": {
                "name": "eastmoney",
                "type": "public_http",
                "channel": "zt_pool",
            },
            "trade_date": trade_date.isoformat(),
            "total_count": len(records),
            "limit_up_stocks": records,
        }

    def fetch_leaderboard(
        self,
        *,
        rank_type: str,
        limit: int,
    ) -> dict[str, object]:
        rank_config = LEADERBOARD_PARAM_MAP.get(rank_type)
        if rank_config is None:
            raise ValueError(f"unsupported leaderboard rank type: {rank_type}")

        page_size = max(1, min(int(limit), 100))
        response = self.session.get(
            EASTMONEY_LEADERBOARD_URL,
            params={
                "pn": 1,
                "pz": page_size,
                "po": rank_config["po"],
                "np": 1,
                "ut": EASTMONEY_LIMIT_UP_UT,
                "fltt": 2,
                "invt": 2,
                "fid": rank_config["fid"],
                "fs": EASTMONEY_A_STOCK_FS,
                "fields": "f12,f14,f2,f3,f6,f7,f8,f9,f10",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("eastmoney leaderboard response must be a JSON object")
        if payload.get("rc") not in (0, "0", None):
            raise ValueError("eastmoney leaderboard response returned error")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("eastmoney leaderboard response missing data")
        diff = data.get("diff")
        if not isinstance(diff, list):
            raise ValueError("eastmoney leaderboard response missing diff")

        items = [
            _parse_eastmoney_leaderboard_row(item)
            for item in diff
            if isinstance(item, dict)
        ]
        if not items:
            raise ValueError("eastmoney leaderboard response did not contain records")

        return {
            "provider": {
                "name": "eastmoney",
                "type": "public_http",
                "channel": "clist",
            },
            "leaderboard_type": rank_type,
            "total_count": _coerce_int(data.get("total")) or len(items),
            "returned_count": len(items),
            "items": items,
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
        if plan.intent == "limit_up_screen":
            return self.fetch_limit_up_pool(trade_date=date.today())
        if plan.intent == "leaderboard_screen":
            payload = plan.payload or {}
            rank_type = str(payload.get("fallback_type", "gainers"))
            limit = _coerce_int(payload.get("limit")) or 20
            return self.fetch_leaderboard(rank_type=rank_type, limit=limit)
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


def _coerce_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _parse_eastmoney_limit_up_row(row: dict[str, object]) -> dict[str, object]:
    market_code = row.get("m")
    code = str(row.get("c", "")).strip()
    symbol = _eastmoney_symbol(code, market_code)
    if not symbol:
        raise ValueError("eastmoney limit-up row missing usable symbol")

    zttj = row.get("zttj")
    zttj_days = None
    zttj_ct = None
    if isinstance(zttj, dict):
        zttj_days = _coerce_int(zttj.get("days"))
        zttj_ct = _coerce_int(zttj.get("ct"))

    price_raw = _to_float(row.get("p"))
    latest = None if price_raw is None else round(price_raw / 1000, 3)

    return {
        "symbol": symbol,
        "name": str(row.get("n", "")).strip() or None,
        "latest": latest,
        "change_ratio": _to_float(row.get("zdp")),
        "board_count": _coerce_int(row.get("lbc")),
        "first_limit_time": _format_hhmmss(row.get("fbt")),
        "last_limit_time": _format_hhmmss(row.get("lbt")),
        "sector": str(row.get("hybk", "")).strip() or None,
        "sealed_fund": _to_float(row.get("fund")),
        "break_count": _coerce_int(row.get("zbc")),
        "limit_stat_days": zttj_days,
        "limit_stat_count": zttj_ct,
    }


def _parse_eastmoney_leaderboard_row(row: dict[str, object]) -> dict[str, object]:
    code = str(row.get("f12", "")).strip()
    symbol = normalize_symbol(code)
    if not symbol:
        raise ValueError("eastmoney leaderboard row missing usable symbol")

    return {
        "symbol": symbol,
        "name": str(row.get("f14", "")).strip() or None,
        "latest": _to_float(row.get("f2")),
        "change_ratio": _to_float(row.get("f3")),
        "turnover": _to_float(row.get("f6")),
        "amplitude": _to_float(row.get("f7")),
        "turnover_ratio": _to_float(row.get("f8")),
        "pe": _to_float(row.get("f9")),
        "volume_ratio": _to_float(row.get("f10")),
    }


def _eastmoney_symbol(code: str, market_code: object) -> str | None:
    if not code:
        return None
    market = {0: "SZ", 1: "SH", 2: "BJ"}.get(_coerce_int(market_code))
    if market is None:
        if code.startswith(("600", "601", "603", "605", "688")):
            market = "SH"
        elif code.startswith(("4", "8", "92")):
            market = "BJ"
        else:
            market = "SZ"
    return f"{code}.{market}"


def _format_hhmmss(value: object) -> str | None:
    number = _coerce_int(value)
    if number is None:
        return None
    text = f"{number:06d}"
    return f"{text[0:2]}:{text[2:4]}:{text[4:6]}"


def _decode_escaped_text(value: str) -> str:
    if "\\u" not in value:
        return value
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value
