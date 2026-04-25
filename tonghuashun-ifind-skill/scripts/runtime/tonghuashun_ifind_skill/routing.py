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
    "trading_calendar",
    "generic_smart_query",
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

KNOWN_INDEX_ENTITIES = DEFAULT_MARKET_ENTITIES + (
    ("上证50", "000016.SH"),
    ("科创50", "000688.SH"),
    ("中证500", "000905.SH"),
    ("中证1000", "000852.SH"),
    ("北证50", "899050.BJ"),
)

POPULAR_STOCK_ALIASES = {
    "茅台": ("贵州茅台", "600519.SH"),
    "茅子": ("贵州茅台", "600519.SH"),
    "宁王": ("宁德时代", "300750.SZ"),
    "宁德": ("宁德时代", "300750.SZ"),
    "catl": ("宁德时代", "300750.SZ"),
    "迪王": ("比亚迪", "002594.SZ"),
    "比亚迪": ("比亚迪", "002594.SZ"),
    "byd": ("比亚迪", "002594.SZ"),
    "招行": ("招商银行", "600036.SH"),
    "平安银行": ("平安银行", "000001.SZ"),
    "中国平安": ("中国平安", "601318.SH"),
    "平安": ("中国平安", "601318.SH"),
    "中芯国际": ("中芯国际", "688981.SH"),
    "中芯": ("中芯国际", "688981.SH"),
    "迈瑞医疗": ("迈瑞医疗", "300760.SZ"),
    "迈瑞": ("迈瑞医疗", "300760.SZ"),
    "药明康德": ("药明康德", "603259.SH"),
    "药明": ("药明康德", "603259.SH"),
    "东财": ("东方财富", "300059.SZ"),
    "工行": ("工商银行", "601398.SH"),
    "建行": ("建设银行", "601939.SH"),
    "农行": ("农业银行", "601288.SH"),
    "中行": ("中国银行", "601988.SH"),
    "五粮液": ("五粮液", "000858.SZ"),
    "隆基": ("隆基绿能", "601012.SH"),
    "隆基绿能": ("隆基绿能", "601012.SH"),
    "格力": ("格力电器", "000651.SZ"),
    "格力电器": ("格力电器", "000651.SZ"),
    "美的": ("美的集团", "000333.SZ"),
    "美的集团": ("美的集团", "000333.SZ"),
    "万科": ("万科A", "000002.SZ"),
    "万科a": ("万科A", "000002.SZ"),
    "长电": ("长江电力", "600900.SH"),
    "长江电力": ("长江电力", "600900.SH"),
    "紫金": ("紫金矿业", "601899.SH"),
    "紫金矿业": ("紫金矿业", "601899.SH"),
    "中信证券": ("中信证券", "600030.SH"),
    "海康": ("海康威视", "002415.SZ"),
    "海康威视": ("海康威视", "002415.SZ"),
    "伊利": ("伊利股份", "600887.SH"),
    "伊利股份": ("伊利股份", "600887.SH"),
    "牧原": ("牧原股份", "002714.SZ"),
    "牧原股份": ("牧原股份", "002714.SZ"),
    "立讯": ("立讯精密", "002475.SZ"),
    "立讯精密": ("立讯精密", "002475.SZ"),
    "恒瑞": ("恒瑞医药", "600276.SH"),
    "恒瑞医药": ("恒瑞医药", "600276.SH"),
    "万华": ("万华化学", "600309.SH"),
    "万华化学": ("万华化学", "600309.SH"),
    "三一": ("三一重工", "600031.SH"),
    "三一重工": ("三一重工", "600031.SH"),
    "海尔": ("海尔智家", "600690.SH"),
    "海尔智家": ("海尔智家", "600690.SH"),
    "中兴": ("中兴通讯", "000063.SZ"),
    "中兴通讯": ("中兴通讯", "000063.SZ"),
    "京东方": ("京东方A", "000725.SZ"),
    "京东方a": ("京东方A", "000725.SZ"),
    "tcl科技": ("TCL科技", "000100.SZ"),
    "寒武纪": ("寒武纪", "688256.SH"),
    "中际旭创": ("中际旭创", "300308.SZ"),
    "新易盛": ("新易盛", "300502.SZ"),
}

INDEX_ALIASES = {
    "上证指数": ("上证指数", "000001.SH"),
    "上证综指": ("上证指数", "000001.SH"),
    "上证": ("上证指数", "000001.SH"),
    "沪指": ("上证指数", "000001.SH"),
    "深证成指": ("深证成指", "399001.SZ"),
    "深成指": ("深证成指", "399001.SZ"),
    "深指": ("深证成指", "399001.SZ"),
    "创业板指": ("创业板指", "399006.SZ"),
    "创业板指数": ("创业板指", "399006.SZ"),
    "创业板": ("创业板指", "399006.SZ"),
    "沪深300": ("沪深300", "000300.SH"),
    "hs300": ("沪深300", "000300.SH"),
    "上证50": ("上证50", "000016.SH"),
    "sz50": ("上证50", "000016.SH"),
    "科创50": ("科创50", "000688.SH"),
    "科创板50": ("科创50", "000688.SH"),
    "中证500": ("中证500", "000905.SH"),
    "zz500": ("中证500", "000905.SH"),
    "中证1000": ("中证1000", "000852.SH"),
    "zz1000": ("中证1000", "000852.SH"),
    "北证50": ("北证50", "899050.BJ"),
    "000001.sh": ("上证指数", "000001.SH"),
    "399001.sz": ("深证成指", "399001.SZ"),
    "399006.sz": ("创业板指", "399006.SZ"),
    "000300.sh": ("沪深300", "000300.SH"),
    "000016.sh": ("上证50", "000016.SH"),
    "000688.sh": ("科创50", "000688.SH"),
    "000905.sh": ("中证500", "000905.SH"),
    "000852.sh": ("中证1000", "000852.SH"),
    "899050.bj": ("北证50", "899050.BJ"),
}

_ETF_SH_PREFIXES = ("50", "51", "52", "56", "58")
_ETF_SZ_PREFIXES = ("15", "16", "18")
_SYMBOL_RE = re.compile(
    r"(?i)(?<![A-Z0-9.])(?:SH|SZ|BJ)?\d{6}(?:\.(?:SH|SZ|BJ)|(?:SH|SZ|BJ))?(?![A-Z0-9.])"
)
_DATE_RANGE_RE = re.compile(r"(?P<start>\d{4}-\d{2}-\d{2}).*?(?P<end>\d{4}-\d{2}-\d{2})")
_SINGLE_DATE_RE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")
_MONTH_DAY_RE = re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})[日号]?")
_MANUAL_LOOKUP_PATTERNS = ("pdf", "下载链接", "全文下载", "原文")
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
_PRECISE_FINANCIAL_METRIC_PATTERNS = (
    "营收",
    "营业收入",
    "营业总收入",
    "收入",
    "毛利率",
    "净利率",
    "净利润",
    "扣非",
    "roe",
    "资产负债率",
    "现金流",
    "市盈率",
    "市净率",
    "pe",
    "pb",
    "市值",
    "总市值",
    "流通市值",
    "同比",
    "环比",
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
_MARKET_PATTERNS = (
    "大盘",
    "盘面",
    "市场表现",
    "市场快照",
    "指数",
    "a股",
    "沪指",
    "深指",
    "创业板",
)
_LIMIT_UP_PATTERNS = ("涨停", "涨停板", "封板")
_LEADERBOARD_PATTERNS = ("榜", "排行", "排名", "top", "前十", "前二十", "前30", "前50")
_PROFILE_PATTERNS = (
    "主营业务",
    "公司简介",
    "公司介绍",
    "干啥",
    "干什么",
    "做什么",
    "是做什么的",
    "业务是什么",
    "属于什么行业",
)
_TRADING_CALENDAR_PATTERNS = (
    "交易日",
    "休市",
    "开不开盘",
    "是否开盘",
    "是否交易",
)
_CAPITAL_FLOW_PATTERNS = (
    "资金流",
    "主力资金",
    "资金净流入",
    "资金净流出",
    "净流入",
    "净流出",
)
_COMMON_A_SHARE_SMART_PATTERNS = (
    "公告",
    "业绩预告",
    "业绩快报",
    "一季度报告",
    "三季度报告",
    "年度报告",
    "半年报",
    "一季报",
    "三季报",
    "年报",
    "季报",
    "报告",
    "摘要",
    "研报",
    "评级",
    "目标价",
    "消息",
    "新闻",
    "资讯",
    "舆情",
    "龙虎榜",
    "大宗交易",
    "异动",
    "融资融券",
    "融资余额",
    "融券",
    "两融",
    "资金",
    "资金往",
    "主力",
    "外资",
    "北向",
    "沪股通",
    "深股通",
    "陆股通",
    "持股",
    "持仓",
    "股东",
    "十大股东",
    "流通股东",
    "机构持仓",
    "基金持仓",
    "分红",
    "派息",
    "送转",
    "除权",
    "除息",
    "股息率",
    "解禁",
    "限售",
    "停牌",
    "复牌",
    "跌停",
    "风险警示",
    "退市",
    "所属概念",
    "概念",
    "题材",
    "产业链",
    "板块",
    "半导体",
    "新能源",
    "白酒",
    "低估值",
    "便宜",
    "利好",
    "机构",
    "龙头",
    "新股",
    "上市公司",
    "申购",
    "中签",
    "打新",
    "发行价",
    "上市日期",
    "交易日",
    "休市",
)
_PRICE_FIELD_PATTERNS = (
    "开盘价",
    "收盘价",
    "最高价",
    "最低价",
    "成交量",
    "成交额",
    "量比",
)
_QUERY_NOISE_PATTERNS = (
    r"看看",
    r"看下",
    r"看一下",
    r"查下",
    r"查一下",
    r"请问",
    r"麻烦",
    r"帮我",
    r"给我",
    r"我想",
    r"想看",
    r"^看",
    r"^查",
    r"能不能",
    r"能否",
    r"有没有",
    r"有没有相关",
    r"相关",
    r"现在",
    r"目前",
    r"今天",
    r"今日",
    r"昨天",
    r"昨日",
    r"明天",
    r"最近",
    r"近期",
    r"今年",
    r"去年",
    r"下一个",
    r"上一个",
    r"时候",
    r"日期",
    r"最新价",
    r"现价",
    r"股价",
    r"股票",
    r"个股",
    r"行情",
    r"报价",
    r"表现",
    r"怎么样",
    r"咋样",
    r"如何",
    r"还行不",
    r"还能看",
    r"能看",
    r"情况",
    r"记录",
    r"数据",
    r"变化",
    r"安排",
    r"多少",
    r"多少[?？]?",
    r"多少钱",
    r"钱了",
    r"吗",
    r"呢",
    r"吧",
    r"有吗",
    r"有啥",
    r"啥消息",
    r"啥研报",
    r"涨没涨",
    r"涨了没",
    r"涨了吗",
    r"红没红",
    r"红了没",
    r"红了吗",
    r"红了",
    r"绿没绿",
    r"绿了吗",
    r"绿了",
    r"跌没跌",
    r"跌了没",
    r"跌了吗",
    r"跌得多",
    r"跌多",
    r"一下",
    r"一下子",
    r"走势",
    r"历史",
    r"k线",
    r"日k",
    r"周k",
    r"月k",
    r"基本面",
    r"财务",
    r"估值",
    r"开盘价",
    r"收盘价",
    r"最高价",
    r"最低价",
    r"成交量",
    r"成交额",
    r"量比",
    r"换手率",
    r"振幅",
    r"涨跌幅",
    r"涨幅",
    r"跌幅",
    r"价格",
    r"市价",
    r"营业总收入",
    r"营业收入",
    r"营收",
    r"收入",
    r"归母净利润",
    r"扣非净利润",
    r"净利润",
    r"毛利率",
    r"净利率",
    r"资产负债率",
    r"现金流",
    r"总市值",
    r"流通市值",
    r"市盈率",
    r"市净率",
    r"动态pe",
    r"静态pe",
    r"滚动pe",
    r"pe",
    r"pb",
    r"roe",
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
    r"干啥的",
    r"干啥",
    r"干什么",
    r"做什么的",
    r"是做什么的",
    r"属于什么行业",
    r"什么行业",
    r"是什么",
    r"公告",
    r"业绩预告",
    r"业绩快报",
    r"一季度报告",
    r"三季度报告",
    r"年度报告",
    r"半年报",
    r"一季报",
    r"三季报",
    r"年报",
    r"季报",
    r"报告",
    r"摘要",
    r"研报",
    r"评级",
    r"目标价",
    r"新闻",
    r"资讯",
    r"舆情",
    r"龙虎榜",
    r"大宗交易",
    r"异动",
    r"融资融券",
    r"融资余额",
    r"融券",
    r"两融",
    r"北向资金",
    r"北向",
    r"沪股通",
    r"深股通",
    r"陆股通",
    r"十大流通股东",
    r"十大股东",
    r"流通股东",
    r"机构持仓",
    r"基金持仓",
    r"持股",
    r"持仓",
    r"股东",
    r"分红",
    r"派息",
    r"送转",
    r"除权",
    r"除息",
    r"股息率",
    r"时间表",
    r"比例",
    r"解禁",
    r"限售",
    r"停牌",
    r"复牌",
    r"风险警示",
    r"退市",
    r"所属概念",
    r"概念",
    r"题材",
    r"产业链",
    r"板块",
    r"新股",
    r"申购",
    r"中签",
    r"打新",
    r"发行价",
    r"上市日期",
    r"交易日",
    r"休市",
    r"开不开盘",
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

    if _is_blank_or_punctuation_only(normalized_query):
        return _manual_lookup_plan(
            "请输入明确的股票、指数、指标、日期或筛选条件；空白或纯标点无法路由到 iFinD。",
        )

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
    if intent == "trading_calendar":
        return build_trading_calendar_plan(normalized_query, today=effective_today)
    if intent == "market_snapshot":
        return build_market_snapshot_plan(normalized_query)

    entity = _resolve_entity(normalized_query, entity_lookup)
    if entity is None:
        if intent == "quote_realtime" and not _has_generic_query_signal(normalized_query):
            return _manual_lookup_plan(
                "请输入明确的股票、指数、指标、日期或筛选条件；当前问题过于笼统，无法稳定路由到 iFinD。",
            )
        return build_generic_smart_query_plan(normalized_query)

    if intent == "generic_smart_query":
        return build_generic_smart_query_plan(normalized_query, entity=entity)
    if intent == "quote_history":
        return build_history_plan(entity, query=normalized_query, today=effective_today)
    if intent == "fundamental_basic":
        if _is_precise_financial_query(normalized_query):
            return build_generic_smart_query_plan(normalized_query, entity=entity)
        return build_fundamental_plan(entity)
    if intent == "entity_profile":
        return build_entity_profile_plan(entity, normalized_query)
    if entity.entity_type == "index":
        return build_market_snapshot_plan(normalized_query, entity=entity)
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


def build_market_snapshot_plan(
    query: str | None = None,
    *,
    entity: ResolvedEntity | None = None,
) -> RoutePlan:
    entity = entity or resolve_common_index_entity(query or "")
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
    return RoutePlan(
        intent="leaderboard_screen",
        endpoint="/smart_stock_picking",
        payload={
            "searchstring": query,
            "searchtype": "stock",
        },
        entity=None,
    )


def build_entity_profile_plan(entity: ResolvedEntity, query: str) -> RoutePlan:
    return RoutePlan(
        intent="entity_profile",
        endpoint="/smart_stock_picking",
        payload={
            "searchstring": _normalize_entity_profile_query(query, entity),
            "searchtype": "stock",
        },
        entity=entity,
    )


def build_capital_flow_plan(query: str) -> RoutePlan:
    return RoutePlan(
        intent="capital_flow",
        endpoint="/smart_stock_picking",
        payload={"searchstring": query, "searchtype": "stock"},
        entity=None,
    )


def build_generic_smart_query_plan(
    query: str,
    *,
    entity: ResolvedEntity | None = None,
) -> RoutePlan:
    searchstring = _normalize_generic_smart_query(query, entity)
    note = "route_source=ifind_smart_stock_picking"
    if searchstring != query:
        note = f"{note}; normalized_casual_query"
    return RoutePlan(
        intent="generic_smart_query",
        endpoint="/smart_stock_picking",
        payload={"searchstring": searchstring, "searchtype": "stock"},
        entity=entity,
        note=note,
    )


def build_trading_calendar_plan(query: str, *, today: date) -> RoutePlan:
    start = _parse_calendar_start_date(query, today=today)
    end = start + timedelta(days=14)
    return RoutePlan(
        intent="trading_calendar",
        endpoint="/date_sequence",
        payload={
            "codes": "000001.SH",
            "startdate": start.isoformat(),
            "enddate": end.isoformat(),
            "functionpara": {"Days": "Tradedays", "Fill": "Omit"},
            "indipara": [
                {
                    "indicator": "ths_close_price_stock",
                    "indiparams": ["", "100", ""],
                }
            ],
        },
        entity=ResolvedEntity(
            raw="A股交易日历",
            symbol="000001.SH",
            name="上证指数",
            entity_type="index",
        ),
        note="route_source=ifind_date_sequence; response time 字段即 iFinD 返回的交易日序列",
    )


def resolve_common_index_entity(text: str) -> ResolvedEntity | None:
    normalized = (text or "").strip().lower()
    for alias, (name, symbol) in sorted(
        INDEX_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
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
    if len(raw) == 8 and raw[:6].isdigit() and raw[6:] in {"SH", "SZ", "BJ"}:
        return f"{raw[:6]}.{raw[6:]}"
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
    if _is_trading_calendar_query(lowered):
        return "trading_calendar"
    if _is_leaderboard_query(lowered):
        return "leaderboard_screen"
    if any(pattern in lowered for pattern in _PROFILE_PATTERNS):
        return "entity_profile"
    if any(
        pattern in lowered
        for pattern in _FUNDAMENTAL_PATTERNS + _PRECISE_FINANCIAL_METRIC_PATTERNS
    ):
        return "fundamental_basic"
    if any(pattern in lowered for pattern in _COMMON_A_SHARE_SMART_PATTERNS):
        return "generic_smart_query"
    if _looks_like_dated_price_lookup(query, lowered):
        return "quote_history"
    if _DATE_RANGE_RE.search(query) or any(pattern in lowered for pattern in _HISTORY_PATTERNS):
        return "quote_history"
    if any(pattern in lowered for pattern in _MARKET_PATTERNS):
        return "market_snapshot"
    return "quote_realtime"


def _is_leaderboard_query(lowered_query: str) -> bool:
    has_metric = any(
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
    if not has_metric:
        return False
    return any(pattern in lowered_query for pattern in _LEADERBOARD_PATTERNS) or any(
        pattern in lowered_query
        for pattern in (
            "最大",
            "最高",
            "最多",
            "靠前",
            "高的",
            "低的",
            "最好",
            "最差",
        )
    )


def _is_trading_calendar_query(lowered_query: str) -> bool:
    if not any(pattern in lowered_query for pattern in _TRADING_CALENDAR_PATTERNS):
        return False
    stock_lifecycle_terms = ("上市日期", "申购", "中签", "打新", "停牌", "复牌")
    return not any(term in lowered_query for term in stock_lifecycle_terms)


def _needs_manual_lookup(query: str) -> bool:
    lowered = query.lower()
    return any(pattern in lowered for pattern in _MANUAL_LOOKUP_PATTERNS)


def _is_blank_or_punctuation_only(query: str) -> bool:
    return not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", query or "")


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
    alias_entity = resolve_popular_stock_alias(query, entity_hint=entity_hint)
    if alias_entity is not None:
        lookup_entity = None
        if _is_entity_hint_likely_security_name(entity_hint):
            lookup_entity = entity_lookup(entity_hint)
        if lookup_entity is None or _is_alias_lookup_mismatch(alias_entity, lookup_entity):
            return alias_entity
        return lookup_entity
    if not _is_entity_hint_likely_security_name(entity_hint):
        return None
    return entity_lookup(entity_hint)


def resolve_popular_stock_alias(
    text: str,
    *,
    entity_hint: str | None = None,
) -> ResolvedEntity | None:
    normalized_text = (text or "").strip().lower()
    normalized_hint = (entity_hint or "").strip().lower()
    if not normalized_text and not normalized_hint:
        return None

    for alias, (name, symbol) in sorted(
        POPULAR_STOCK_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        normalized_alias = alias.lower()
        if (
            normalized_alias not in normalized_text
            and normalized_alias not in normalized_hint
        ):
            continue
        if _alias_match_is_obviously_not_a_stock(normalized_text, normalized_alias):
            continue
        return ResolvedEntity(
            raw=alias,
            symbol=symbol,
            name=name,
            entity_type="stock",
        )
    return None


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
    stripped = re.sub(r"\d{4}年(?:\d{1,2}月)?(?:\d{1,2}[日号]?)?", " ", stripped)
    stripped = re.sub(r"(?<!\d)\d{4}(?!\d)", " ", stripped)
    stripped = re.sub(r"(?:近|最近)?[一二三四五六七八九十\d]+年", " ", stripped)
    stripped = re.sub(r"(?:近|最近)?[一二三四五六七八九十\d]+(?:个)?季度", " ", stripped)
    stripped = re.sub(r"[，,。？?！!、：:；;（）()【】《》〈〉「」『』\[\]{}\"'“”‘’]", " ", stripped)
    stripped = re.sub(r"\s+", "", stripped)
    return stripped.strip("的和与及是为到至")


def _is_entity_hint_likely_security_name(entity_hint: str) -> bool:
    if not entity_hint:
        return False
    lowered = entity_hint.lower()
    broad_or_condition_terms = (
        "a股",
        "股票",
        "哪些",
        "哪个",
        "什么",
        "下一个",
        "下个",
        "上一个",
        "上个",
        "时候",
        "哪天",
        "日期",
        "多少",
        "啥",
        "买啥",
        "买了啥",
        "卖啥",
        "卖了啥",
        "哪儿",
        "哪里",
        "往哪",
        "往哪里",
        "开不开盘",
        "半导体",
        "新能源",
        "白酒",
        "cpo",
        "算力",
        "机器人",
        "银行股",
        "板块",
        "行业",
        "产业链",
        "概念",
        "龙头",
        "低于",
        "高于",
        "大于",
        "小于",
        "不低于",
        "不高于",
        "近5日",
        "近10日",
        "放量",
        "缩量",
        "申购",
        "中签",
        "交易日",
        "休市",
        "停牌",
        "复牌",
        "跌停",
        "外资",
        "主力",
        "top",
    )
    return not any(term in lowered for term in broad_or_condition_terms)


def _is_alias_lookup_mismatch(
    alias_entity: ResolvedEntity,
    lookup_entity: ResolvedEntity,
) -> bool:
    if lookup_entity.entity_type != "stock":
        return True
    return normalize_symbol(lookup_entity.symbol) != alias_entity.symbol


def _alias_match_is_obviously_not_a_stock(
    normalized_text: str,
    normalized_alias: str,
) -> bool:
    if f"{normalized_alias}市" in normalized_text:
        return True
    if normalized_alias == "药明" and any(
        phrase in normalized_text for phrase in ("药明生物", "港股", "美股", "h股")
    ):
        return True
    return f"{normalized_alias}有哪些" in normalized_text and any(
        term in normalized_text for term in ("上市公司", "地区", "城市", "地方")
    )


def _parse_date_range(query: str, *, today: date) -> tuple[str, str]:
    match = _DATE_RANGE_RE.search(query or "")
    if match:
        return match.group("start"), match.group("end")

    single_date = _extract_single_date(query, today=today)
    if single_date is not None:
        return single_date, single_date

    days = _relative_days(query)
    start = today - timedelta(days=days)
    return start.isoformat(), today.isoformat()


def _extract_single_date(query: str, *, today: date) -> str | None:
    single_date_match = _SINGLE_DATE_RE.search(query or "")
    if single_date_match:
        return single_date_match.group("date")

    month_day_match = _MONTH_DAY_RE.search(query or "")
    if not month_day_match:
        return None
    month = int(month_day_match.group("month"))
    day = int(month_day_match.group("day"))
    try:
        return date(today.year, month, day).isoformat()
    except ValueError:
        return None


def _parse_calendar_start_date(query: str, *, today: date) -> date:
    single_date = _extract_single_date(query, today=today)
    if single_date is not None:
        return date.fromisoformat(single_date)
    lowered = query.lower()
    if "明天" in lowered or "下一个" in lowered or "下个" in lowered:
        return today + timedelta(days=1)
    return today


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


def _looks_like_dated_price_lookup(query: str, lowered_query: str) -> bool:
    has_date = bool(_SINGLE_DATE_RE.search(query or "") or _MONTH_DAY_RE.search(query or ""))
    if not has_date:
        return False
    return any(pattern in lowered_query for pattern in _PRICE_FIELD_PATTERNS)


def _is_precise_financial_query(query: str) -> bool:
    lowered = query.lower()
    return any(pattern in lowered for pattern in _PRECISE_FINANCIAL_METRIC_PATTERNS)


def _normalize_entity_profile_query(query: str, entity: ResolvedEntity) -> str:
    if entity.name and any(term in query for term in ("干啥", "干什么", "做什么")):
        return f"{entity.name}主营业务是什么"
    return query


def _normalize_generic_smart_query(
    query: str,
    entity: ResolvedEntity | None,
) -> str:
    if entity is None or not entity.name:
        if "北向" in query and any(term in query for term in ("买啥", "买了啥", "流入哪些")):
            return "北向资金持股增加前十"
        return query

    casual_terms = ("有啥", "啥", "怎么样", "咋样", "有吗", "消息")
    if not any(term in query for term in casual_terms):
        return query
    if "分红" in query or "派息" in query:
        return f"{entity.name}分红记录"
    if "研报" in query or "评级" in query or "目标价" in query:
        return f"{entity.name}研报"
    if "公告" in query or "消息" in query or "资讯" in query or "新闻" in query:
        return f"{entity.name}最近公告"
    return query


def _has_generic_query_signal(query: str) -> bool:
    lowered = query.lower()
    return any(
        pattern in lowered
        for pattern in (
            _COMMON_A_SHARE_SMART_PATTERNS
            + _CAPITAL_FLOW_PATTERNS
            + _MARKET_PATTERNS
            + _LEADERBOARD_PATTERNS
            + _LIMIT_UP_PATTERNS
        )
    )


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
    return any(symbol == known_symbol for _, known_symbol in KNOWN_INDEX_ENTITIES)


def _known_index_name(symbol: str) -> str | None:
    for name, known_symbol in KNOWN_INDEX_ENTITIES:
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
