from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import timedelta
import re
from typing import Callable
from typing import Literal


Intent = Literal[
    "quote_realtime",
    "quote_history",
    "market_snapshot",
    "fundamental_basic",
    "limit_up_screen",
    "leaderboard_screen",
    "entity_profile",
    "capital_flow",
    "manual_lookup",
]
EntityType = Literal["stock", "index"]


HISTORY_INDICATORS = "open,high,low,close,volume,amount,changeRatio"
REALTIME_INDICATORS = (
    "open,high,low,latest,changeRatio,change,preClose,"
    "volume,amount,turnoverRatio,volumeRatio,amplitude,pb"
)
MARKET_SNAPSHOT_INDICATORS = "open,high,low,latest,changeRatio,change,preClose,volume,amount"

FINANCIAL_QUERY_TEMPLATE = (
    "{target} 营业总收入 归属于母公司所有者的净利润 扣除非经常性损益后的净利润 "
    "销售毛利率 销售净利率 净资产收益率roe 资产负债率 经营活动产生的现金流量净额 存货"
)
VALUATION_QUERY_TEMPLATE = "{target} 量比 换手率 市盈率 市净率 总市值 流通市值"
FORECAST_QUERY_TEMPLATE = "{target} 预测净利润平均值 预测主营业务收入平均值 2026 2027"

DEFAULT_MARKET_ENTITIES = (
    ("上证指数", "000001.SH"),
    ("深证成指", "399001.SZ"),
    ("创业板指", "399006.SZ"),
    ("沪深300", "000300.SH"),
)

INDEX_ALIASES = {
    "上证指数": ("上证指数", "000001.SH"),
    "上证综指": ("上证指数", "000001.SH"),
    "上证": ("上证指数", "000001.SH"),
    "深证成指": ("深证成指", "399001.SZ"),
    "深成指": ("深证成指", "399001.SZ"),
    "创业板指": ("创业板指", "399006.SZ"),
    "沪深300": ("沪深300", "000300.SH"),
    "hs300": ("沪深300", "000300.SH"),
    "000001.sh": ("上证指数", "000001.SH"),
    "399001.sz": ("深证成指", "399001.SZ"),
    "399006.sz": ("创业板指", "399006.SZ"),
    "000300.sh": ("沪深300", "000300.SH"),
}

_ETF_SH_PREFIXES = ("50", "51", "52", "56", "58")
_ETF_SZ_PREFIXES = ("15", "16", "18")
_SYMBOL_RE = re.compile(r"(?i)\b(?:sh|sz|bj)?\d{6}(?:\.(?:sh|sz|bj))?\b")
_DATE_RANGE_RE = re.compile(r"(?P<start>\d{4}-\d{2}-\d{2}).*?(?P<end>\d{4}-\d{2}-\d{2})")
_MANUAL_LOOKUP_PATTERNS = ("公告", "pdf", "下载链接", "全文下载", "原文")
_FUNDAMENTAL_PATTERNS = (
    "基本面",
    "财务",
    "估值",
    "营收",
    "净利润",
    "roe",
    "市盈率",
    "市净率",
    "pe",
    "pb",
    "市值",
)
_HISTORY_PATTERNS = (
    "历史",
    "走势",
    "k线",
    "日k",
    "周k",
    "月k",
    "近一个月",
    "最近一个月",
    "近1个月",
    "近一周",
    "最近一周",
    "近1周",
    "近三个月",
    "最近三个月",
    "近3个月",
    "近半年",
    "近一年",
)
_MARKET_PATTERNS = ("大盘", "盘面", "市场表现", "市场快照", "指数")
_LIMIT_UP_PATTERNS = ("涨停", "涨停板", "封板")
_LEADERBOARD_PATTERNS = ("榜", "排行", "排名", "top", "前十", "前二十", "前30", "前50")
_PROFILE_PATTERNS = (
    "主营业务",
    "公司简介",
    "公司介绍",
    "做什么",
    "是做什么的",
    "业务是什么",
    "属于什么行业",
)
_CAPITAL_FLOW_PATTERNS = (
    "资金流",
    "主力资金",
    "资金净流入",
    "资金净流出",
    "净流入",
    "净流出",
)
_QUERY_NOISE_PATTERNS = (
    r"看看?",
    r"看下",
    r"看一下",
    r"查下",
    r"查一下",
    r"帮我",
    r"给我",
    r"现在",
    r"目前",
    r"最新价",
    r"现价",
    r"股价",
    r"行情",
    r"报价",
    r"走势",
    r"历史",
    r"k线",
    r"日k",
    r"周k",
    r"月k",
    r"基本面",
    r"财务",
    r"估值",
    r"大盘",
    r"指数",
    r"近一个月",
    r"最近一个月",
    r"近1个月",
    r"近一周",
    r"最近一周",
    r"近1周",
    r"近三个月",
    r"最近三个月",
    r"近3个月",
    r"近半年",
    r"近一年",
    r"近\d+天",
    r"主营业务是什么",
    r"主营业务",
    r"业务是什么",
    r"公司简介",
    r"公司介绍",
    r"做什么的",
    r"是做什么的",
    r"属于什么行业",
    r"什么行业",
    r"是什么",
)


@dataclass(frozen=True)
class ResolvedEntity:
    raw: str
    symbol: str
    name: str | None
    entity_type: EntityType


@dataclass(frozen=True)
class RoutePlan:
    intent: Intent
    endpoint: str | None
    payload: dict[str, object] | None
    entity: ResolvedEntity | None
    note: str | None = None


def build_route_plan(
    query: str,
    *,
    entity_lookup: Callable[[str], ResolvedEntity | None],
    today: date | None = None,
) -> RoutePlan:
    normalized_query = (query or "").strip()
    effective_today = today or date.today()

    if _needs_manual_lookup(normalized_query):
        return _manual_lookup_plan(
            "这个请求不在内置常见路由里。请先阅读 references/routing.md，再决定是否用 api-call；如果文档里也没有合适接口，就明确告诉用户当前 skill 未覆盖该 iFinD 能力。",
        )

    intent = _detect_intent(normalized_query)
    if intent == "limit_up_screen":
        return build_limit_up_plan(normalized_query)
    if intent == "leaderboard_screen":
        return build_leaderboard_plan(normalized_query)
    if intent == "capital_flow":
        return build_capital_flow_plan(normalized_query)
    if intent == "market_snapshot":
        return build_market_snapshot_plan(normalized_query)

    entity = _resolve_entity(normalized_query, entity_lookup)
    if entity is None:
        return _manual_lookup_plan(
            "无法从请求中稳定解析股票或指数标的。请先阅读 references/routing.md；如果仍无法确定接口和标的，请告诉用户当前 skill 不能可靠处理该请求。",
        )

    if intent == "quote_history":
        return build_history_plan(entity, query=normalized_query, today=effective_today)
    if intent == "fundamental_basic":
        return build_fundamental_plan(entity)
    if intent == "entity_profile":
        return build_entity_profile_plan(entity, normalized_query)
    return build_realtime_plan(entity)


def build_realtime_plan(entity: ResolvedEntity) -> RoutePlan:
    indicators = (
        MARKET_SNAPSHOT_INDICATORS
        if entity.entity_type == "index"
        else REALTIME_INDICATORS
    )
    return RoutePlan(
        intent="quote_realtime",
        endpoint="/real_time_quotation",
        payload={"codes": entity.symbol, "indicators": indicators},
        entity=entity,
    )


def build_history_plan(
    entity: ResolvedEntity,
    *,
    query: str,
    today: date,
    start_date: str | None = None,
    end_date: str | None = None,
) -> RoutePlan:
    start_value, end_value = _parse_date_range(query, today=today)
    if start_date:
        start_value = start_date
    if end_date:
        end_value = end_date
    return RoutePlan(
        intent="quote_history",
        endpoint="/cmd_history_quotation",
        payload={
            "codes": entity.symbol,
            "indicators": HISTORY_INDICATORS,
            "startdate": start_value,
            "enddate": end_value,
        },
        entity=entity,
    )


def build_market_snapshot_plan(query: str | None = None) -> RoutePlan:
    entity = resolve_common_index_entity(query or "")
    if entity is not None:
        codes = entity.symbol
    else:
        codes = ",".join(symbol for _, symbol in DEFAULT_MARKET_ENTITIES)
    return RoutePlan(
        intent="market_snapshot",
        endpoint="/real_time_quotation",
        payload={"codes": codes, "indicators": MARKET_SNAPSHOT_INDICATORS},
        entity=entity,
    )


def build_fundamental_plan(entity: ResolvedEntity) -> RoutePlan:
    target = entity.symbol
    return RoutePlan(
        intent="fundamental_basic",
        endpoint="/smart_stock_picking",
        payload={
            "searchstrings": [
                FINANCIAL_QUERY_TEMPLATE.format(target=target),
                VALUATION_QUERY_TEMPLATE.format(target=target),
                FORECAST_QUERY_TEMPLATE.format(target=target),
            ],
            "searchtype": "stock",
        },
        entity=entity,
    )


def build_limit_up_plan(query: str) -> RoutePlan:
    return RoutePlan(
        intent="limit_up_screen",
        endpoint="/smart_stock_picking",
        payload={"searchstring": query, "searchtype": "stock"},
        entity=None,
    )


def build_leaderboard_plan(query: str) -> RoutePlan:
    fallback_type = _leaderboard_fallback_type(query)
    return RoutePlan(
        intent="leaderboard_screen",
        endpoint="/smart_stock_picking",
        payload={
            "searchstring": query,
            "searchtype": "stock",
            "fallback_type": fallback_type,
            "limit": _extract_rank_limit(query),
        },
        entity=None,
    )


def build_entity_profile_plan(entity: ResolvedEntity, query: str) -> RoutePlan:
    return RoutePlan(
        intent="entity_profile",
        endpoint="/smart_stock_picking",
        payload={"searchstring": query, "searchtype": "stock"},
        entity=entity,
    )


def build_capital_flow_plan(query: str) -> RoutePlan:
    return RoutePlan(
        intent="capital_flow",
        endpoint="/smart_stock_picking",
        payload={"searchstring": query, "searchtype": "stock"},
        entity=None,
    )


def resolve_common_index_entity(text: str) -> ResolvedEntity | None:
    normalized = (text or "").strip().lower()
    for alias, (name, symbol) in INDEX_ALIASES.items():
        if alias in normalized:
            return ResolvedEntity(raw=text, symbol=symbol, name=name, entity_type="index")
    return None


def extract_entity_from_search_payload(raw: str, payload: dict[str, object]) -> ResolvedEntity | None:
    if not isinstance(payload, dict):
        return None
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables:
        return None
    first = tables[0]
    if not isinstance(first, dict):
        return None
    table = first.get("table")
    if not isinstance(table, dict):
        return None

    symbol = _first_text(table, ("股票代码", "证券代码", "thscode"))
    if not symbol:
        return None
    normalized_symbol = normalize_symbol(symbol)
    name = _first_text(table, ("股票简称", "证券简称", "股票名称", "证券名称"))
    entity_type: EntityType = "index" if _is_known_index_symbol(normalized_symbol) else "stock"
    return ResolvedEntity(raw=raw, symbol=normalized_symbol, name=name, entity_type=entity_type)


def normalize_symbol(text: str) -> str:
    raw = (text or "").strip().upper()
    if not raw:
        return raw
    if raw in {"000001.SH", "399001.SZ", "399006.SZ", "000300.SH"}:
        return raw
    if raw.startswith(("SH", "SZ", "BJ")) and raw[2:].isdigit():
        return f"{raw[2:]}.{raw[:2]}"
    if "." in raw:
        code, market = raw.split(".", 1)
        market = market.upper()
        return f"{code}.{market}"
    if not raw.isdigit() or len(raw) != 6:
        return raw
    if raw.startswith(_ETF_SH_PREFIXES):
        return f"{raw}.SH"
    if raw.startswith(_ETF_SZ_PREFIXES):
        return f"{raw}.SZ"
    if _is_bse_code(raw):
        return f"{raw}.BJ"
    if raw.startswith(("600", "601", "603", "605", "688")):
        return f"{raw}.SH"
    return f"{raw}.SZ"


def _detect_intent(query: str) -> Intent:
    lowered = query.lower()
    if any(pattern in lowered for pattern in _LIMIT_UP_PATTERNS):
        return "limit_up_screen"
    if any(pattern in lowered for pattern in _CAPITAL_FLOW_PATTERNS):
        return "capital_flow"
    if _is_leaderboard_query(lowered):
        return "leaderboard_screen"
    if any(pattern in lowered for pattern in _PROFILE_PATTERNS):
        return "entity_profile"
    if any(pattern in lowered for pattern in _FUNDAMENTAL_PATTERNS):
        return "fundamental_basic"
    if _DATE_RANGE_RE.search(query) or any(pattern in lowered for pattern in _HISTORY_PATTERNS):
        return "quote_history"
    if any(pattern in lowered for pattern in _MARKET_PATTERNS):
        return "market_snapshot"
    return "quote_realtime"


def _is_leaderboard_query(lowered_query: str) -> bool:
    if not any(pattern in lowered_query for pattern in _LEADERBOARD_PATTERNS):
        return False
    return any(
        pattern in lowered_query
        for pattern in (
            "成交额",
            "成交金额",
            "涨幅",
            "跌幅",
            "换手率",
            "振幅",
            "量比",
            "领涨",
            "领跌",
        )
    )


def _needs_manual_lookup(query: str) -> bool:
    lowered = query.lower()
    return any(pattern in lowered for pattern in _MANUAL_LOOKUP_PATTERNS)


def _resolve_entity(
    query: str,
    entity_lookup: Callable[[str], ResolvedEntity | None],
) -> ResolvedEntity | None:
    index_entity = resolve_common_index_entity(query)
    if index_entity is not None:
        return index_entity

    symbol_candidate = _extract_symbol_candidate(query)
    if symbol_candidate:
        normalized_symbol = normalize_symbol(symbol_candidate)
        entity_type: EntityType = "index" if _is_known_index_symbol(normalized_symbol) else "stock"
        known_name = _known_index_name(normalized_symbol)
        return ResolvedEntity(
            raw=symbol_candidate,
            symbol=normalized_symbol,
            name=known_name,
            entity_type=entity_type,
        )

    entity_hint = _extract_entity_hint(query)
    if not entity_hint:
        return None
    return entity_lookup(entity_hint)


def _extract_symbol_candidate(query: str) -> str | None:
    match = _SYMBOL_RE.search(query or "")
    if not match:
        return None
    return match.group(0)


def _extract_entity_hint(query: str) -> str:
    stripped = query or ""
    for pattern in _QUERY_NOISE_PATTERNS:
        stripped = re.sub(pattern, " ", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\d{4}-\d{2}-\d{2}", " ", stripped)
    stripped = re.sub(r"\s+", "", stripped)
    return stripped


def _parse_date_range(query: str, *, today: date) -> tuple[str, str]:
    match = _DATE_RANGE_RE.search(query or "")
    if match:
        return match.group("start"), match.group("end")

    days = _relative_days(query)
    start = today - timedelta(days=days)
    return start.isoformat(), today.isoformat()


def _relative_days(query: str) -> int:
    lowered = query.lower()
    explicit_days = re.search(r"近(\d+)天", lowered)
    if explicit_days:
        return max(int(explicit_days.group(1)), 1)
    if any(pattern in lowered for pattern in ("近一周", "最近一周", "近1周")):
        return 7
    if any(pattern in lowered for pattern in ("近一个月", "最近一个月", "近1个月")):
        return 30
    if any(pattern in lowered for pattern in ("近三个月", "最近三个月", "近3个月")):
        return 90
    if "近半年" in lowered:
        return 180
    if "近一年" in lowered:
        return 365
    return 30


def _leaderboard_fallback_type(query: str) -> str:
    lowered = query.lower()
    if "成交额" in lowered or "成交金额" in lowered:
        return "turnover"
    if "换手率" in lowered:
        return "turnover_ratio"
    if "振幅" in lowered:
        return "amplitude"
    if "量比" in lowered:
        return "volume_ratio"
    if "跌幅" in lowered or "领跌" in lowered:
        return "losers"
    return "gainers"


def _extract_rank_limit(query: str) -> int:
    lowered = query.lower()
    english_match = re.search(r"top\s*(\d+)", lowered)
    if english_match:
        return max(1, int(english_match.group(1)))

    digits_match = re.search(r"前\s*(\d+)", lowered)
    if digits_match:
        return max(1, int(digits_match.group(1)))

    chinese_match = re.search(r"前([一二三四五六七八九十两百]+)", lowered)
    if chinese_match:
        parsed = _parse_chinese_number(chinese_match.group(1))
        if parsed is not None:
            return max(1, parsed)
    return 20


def _parse_chinese_number(text: str) -> int | None:
    values = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "百": 100,
    }
    cleaned = text.strip()
    if not cleaned:
        return None
    if cleaned == "十":
        return 10
    if "百" in cleaned:
        parts = cleaned.split("百", 1)
        hundreds = values.get(parts[0], 1)
        rest = _parse_chinese_number(parts[1]) if parts[1] else 0
        if hundreds is None or rest is None:
            return None
        return hundreds * 100 + rest
    if "十" in cleaned:
        parts = cleaned.split("十", 1)
        tens = values.get(parts[0], 1) if parts[0] else 1
        units = values.get(parts[1], 0) if parts[1] else 0
        if tens is None or units is None:
            return None
        return tens * 10 + units
    return values.get(cleaned)


def _manual_lookup_plan(note: str) -> RoutePlan:
    return RoutePlan(
        intent="manual_lookup",
        endpoint=None,
        payload=None,
        entity=None,
        note=note,
    )


def _is_bse_code(code: str) -> bool:
    return len(code) == 6 and code.isdigit() and code.startswith(("4", "8", "92"))


def _is_known_index_symbol(symbol: str) -> bool:
    return any(symbol == known_symbol for _, known_symbol in DEFAULT_MARKET_ENTITIES)


def _known_index_name(symbol: str) -> str | None:
    for name, known_symbol in DEFAULT_MARKET_ENTITIES:
        if symbol == known_symbol:
            return name
    return None


def _first_text(table: dict[str, object], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = table.get(key)
        if isinstance(value, list):
            value = value[0] if value else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
