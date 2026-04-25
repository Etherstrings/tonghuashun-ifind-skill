from __future__ import annotations

from datetime import date

from tonghuashun_ifind_skill.routing import ResolvedEntity
from tonghuashun_ifind_skill.routing import build_route_plan


COMMON_A_SHARE_ENTITIES = {
    "贵州茅台": ("600519.SH", "贵州茅台"),
    "宁德时代": ("300750.SZ", "宁德时代"),
    "比亚迪": ("002594.SZ", "比亚迪"),
    "招商银行": ("600036.SH", "招商银行"),
    "中国平安": ("601318.SH", "中国平安"),
    "中芯国际": ("688981.SH", "中芯国际"),
    "迈瑞医疗": ("300760.SZ", "迈瑞医疗"),
    "药明康德": ("603259.SH", "药明康德"),
    "东方财富": ("300059.SZ", "东方财富"),
    "工商银行": ("601398.SH", "工商银行"),
}


def common_a_share_entity_lookup(text: str) -> ResolvedEntity | None:
    if "贵州茅台" in text:
        return ResolvedEntity(
            raw="贵州茅台",
            symbol="600519.SH",
            name="贵州茅台",
            entity_type="stock",
        )
    if "宁德时代" in text:
        return ResolvedEntity(
            raw="宁德时代",
            symbol="300750.SZ",
            name="宁德时代",
            entity_type="stock",
        )
    return None


def exact_common_a_share_entity_lookup(text: str) -> ResolvedEntity | None:
    match = COMMON_A_SHARE_ENTITIES.get(text)
    if match is None:
        return None
    symbol, name = match
    return ResolvedEntity(raw=text, symbol=symbol, name=name, entity_type="stock")


def test_realtime_route_uses_real_time_quotation_for_stock_price_query():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(
            raw="贵州茅台",
            symbol="600519.SH",
            name="贵州茅台",
            entity_type="stock",
        )

    plan = build_route_plan(
        "看看贵州茅台现在股价",
        entity_lookup=lookup,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "quote_realtime"
    assert plan.endpoint == "/real_time_quotation"
    assert plan.payload["codes"] == "600519.SH"


def test_chinese_stock_name_with_question_noise_resolves_to_symbol():
    captured: list[str] = []

    def lookup(text: str) -> ResolvedEntity | None:
        captured.append(text)
        if text == "贵州茅台":
            return ResolvedEntity(
                raw=text,
                symbol="600519.SH",
                name="贵州茅台",
                entity_type="stock",
            )
        return None

    plan = build_route_plan(
        "请问贵州茅台最近股价怎么样",
        entity_lookup=lookup,
        today=date(2026, 4, 25),
    )

    assert captured == ["贵州茅台"]
    assert plan.intent == "quote_realtime"
    assert plan.endpoint == "/real_time_quotation"
    assert plan.payload["codes"] == "600519.SH"


def test_history_route_parses_relative_one_month_window():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(
            raw="宁德时代",
            symbol="300750.SZ",
            name="宁德时代",
            entity_type="stock",
        )

    plan = build_route_plan(
        "看下宁德时代近一个月走势",
        entity_lookup=lookup,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "quote_history"
    assert plan.endpoint == "/cmd_history_quotation"
    assert plan.payload["codes"] == "300750.SZ"
    assert plan.payload["startdate"] == "2026-03-17"
    assert plan.payload["enddate"] == "2026-04-16"


def test_single_day_price_query_routes_to_history_with_same_day_window():
    plan = build_route_plan(
        "600004 4月21号 开盘价 收盘价 量比",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 21),
    )

    assert plan.intent == "quote_history"
    assert plan.endpoint == "/cmd_history_quotation"
    assert plan.payload["codes"] == "600004.SH"
    assert plan.payload["startdate"] == "2026-04-21"
    assert plan.payload["enddate"] == "2026-04-21"
    assert "include_volume_ratio" not in plan.payload


def test_market_snapshot_defaults_to_major_indices_for_market_query():
    plan = build_route_plan(
        "看一下大盘",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "market_snapshot"
    assert plan.endpoint == "/real_time_quotation"
    assert plan.payload["codes"] == "000001.SH,399001.SZ,399006.SZ,000300.SH"


def test_fundamental_route_builds_three_smart_pick_queries():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(
            raw="宁德时代",
            symbol="300750.SZ",
            name="宁德时代",
            entity_type="stock",
        )

    plan = build_route_plan(
        "看看宁德时代基本面",
        entity_lookup=lookup,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "fundamental_basic"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.payload["searchstrings"] == [
        "300750.SZ 营业总收入 归属于母公司所有者的净利润 扣除非经常性损益后的净利润 销售毛利率 销售净利率 净资产收益率roe 资产负债率 经营活动产生的现金流量净额 存货",
        "300750.SZ 量比 换手率 市盈率 市净率 总市值 流通市值",
        "300750.SZ 预测净利润平均值 预测主营业务收入平均值 2026 2027",
    ]


def test_precise_financial_natural_language_preserves_original_query():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(
            raw="贵州茅台",
            symbol="600519.SH",
            name="贵州茅台",
            entity_type="stock",
        )

    plan = build_route_plan(
        "查一下贵州茅台近三年营收和毛利率",
        entity_lookup=lookup,
        today=date(2026, 4, 25),
    )

    assert plan.intent == "generic_smart_query"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is not None
    assert plan.entity.symbol == "600519.SH"
    assert plan.payload == {
        "searchstring": "查一下贵州茅台近三年营收和毛利率",
        "searchtype": "stock",
    }


def test_specific_financial_metrics_preserve_original_query():
    plan = build_route_plan(
        "宁德时代市盈率和总市值是多少",
        entity_lookup=common_a_share_entity_lookup,
        today=date(2026, 4, 25),
    )

    assert plan.intent == "generic_smart_query"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is not None
    assert plan.entity.symbol == "300750.SZ"
    assert plan.payload == {
        "searchstring": "宁德时代市盈率和总市值是多少",
        "searchtype": "stock",
    }


def test_common_a_share_entity_queries_preserve_original_query():
    queries = [
        "贵州茅台最近公告",
        "贵州茅台分红记录",
        "贵州茅台龙虎榜",
        "宁德时代融资余额和北向持股情况",
        "宁德时代限售解禁安排",
        "宁德时代所属概念和产业链",
    ]

    for query in queries:
        plan = build_route_plan(
            query,
            entity_lookup=common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query"
        assert plan.endpoint == "/smart_stock_picking"
        assert plan.entity is not None
        assert plan.payload == {
            "searchstring": query,
            "searchtype": "stock",
        }


def test_common_a_share_market_queries_without_entity_use_ifind_smart_pick():
    queries = [
        "明天A股有哪些新股申购",
        "今天有哪些股票停牌复牌",
        "半导体板块最近有什么研报和评级变化",
    ]

    for query in queries:
        plan = build_route_plan(
            query,
            entity_lookup=lambda _: None,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query"
        assert plan.endpoint == "/smart_stock_picking"
        assert plan.entity is None
        assert plan.payload == {
            "searchstring": query,
            "searchtype": "stock",
        }


def test_broad_market_smart_queries_do_not_call_entity_lookup():
    queries = [
        "明天A股有哪些新股申购",
        "今天有哪些股票停牌复牌",
        "半导体板块里市盈率低于30且近5日放量的股票",
    ]

    def fail_lookup(text: str) -> ResolvedEntity | None:
        raise AssertionError(f"broad market query should not lookup entity: {text}")

    for query in queries:
        plan = build_route_plan(
            query,
            entity_lookup=fail_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query", query
        assert plan.endpoint == "/smart_stock_picking", query
        assert plan.entity is None, query
        assert plan.payload == {
            "searchstring": query,
            "searchtype": "stock",
        }, query


def test_limit_up_query_routes_to_smart_stock_picking_without_entity_lookup():
    plan = build_route_plan(
        "今天的A股涨停数据",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 20),
    )

    assert plan.intent == "limit_up_screen"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is None
    assert plan.payload == {
        "searchstring": "今天的A股涨停数据",
        "searchtype": "stock",
    }


def test_leaderboard_query_routes_to_leaderboard_intent():
    plan = build_route_plan(
        "A股成交额榜前十",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 20),
    )

    assert plan.intent == "leaderboard_screen"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is None
    assert plan.payload == {
        "searchstring": "A股成交额榜前十",
        "searchtype": "stock",
    }


def test_stock_profile_query_routes_to_profile_intent():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(
            raw="贵州茅台",
            symbol="600519.SH",
            name="贵州茅台",
            entity_type="stock",
        )

    plan = build_route_plan(
        "贵州茅台主营业务是什么",
        entity_lookup=lookup,
        today=date(2026, 4, 20),
    )

    assert plan.intent == "entity_profile"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is not None
    assert plan.entity.symbol == "600519.SH"


def test_capital_flow_query_routes_to_capital_flow_intent():
    plan = build_route_plan(
        "今天主力资金流入前十",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 20),
    )

    assert plan.intent == "capital_flow"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is None
    assert plan.payload == {
        "searchstring": "今天主力资金流入前十",
        "searchtype": "stock",
    }


def test_complex_unmatched_query_routes_to_ifind_smart_pick():
    plan = build_route_plan(
        "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 20),
    )

    assert plan.intent == "generic_smart_query"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is None
    assert plan.payload == {
        "searchstring": "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票",
        "searchtype": "stock",
    }


def test_unsupported_query_returns_manual_lookup_required():
    plan = build_route_plan(
        "帮我找贵州茅台公告PDF下载链接并按日期排序",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "manual_lookup"
    assert plan.endpoint is None
    assert "references/routing.md" in (plan.note or "")


def test_blank_or_punctuation_only_query_requires_clearer_input():
    for query in ("", "   ", "？？？", "!!!"):
        plan = build_route_plan(
            query,
            entity_lookup=lambda _: None,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "manual_lookup", query
        assert plan.endpoint is None, query
        assert "空白或纯标点" in (plan.note or ""), query


def test_vague_casual_query_requires_clearer_input_without_ifind_lookup():
    def fail_lookup(text: str) -> ResolvedEntity | None:
        raise AssertionError(f"vague query should not lookup entity: {text}")

    plan = build_route_plan(
        "帮我看看",
        entity_lookup=fail_lookup,
        today=date(2026, 4, 25),
    )

    assert plan.intent == "manual_lookup"
    assert plan.endpoint is None
    assert "过于笼统" in (plan.note or "")


def test_announcement_summary_is_supported_but_pdf_download_requires_manual_lookup():
    supported_plan = build_route_plan(
        "贵州茅台最近公告",
        entity_lookup=common_a_share_entity_lookup,
        today=date(2026, 4, 25),
    )
    manual_plan = build_route_plan(
        "帮我找贵州茅台公告PDF下载链接并按日期排序",
        entity_lookup=common_a_share_entity_lookup,
        today=date(2026, 4, 25),
    )

    assert supported_plan.intent == "generic_smart_query"
    assert supported_plan.endpoint == "/smart_stock_picking"
    assert manual_plan.intent == "manual_lookup"
    assert manual_plan.endpoint is None


def test_natural_language_route_matrix_for_core_a_share_queries():
    cases = [
        ("贵州茅台最新价", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("中国平安现在股价", "quote_realtime", "/real_time_quotation", "601318.SH"),
        ("看贵州茅台行情", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("查贵州茅台行情", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("招商银行收盘价多少", "quote_realtime", "/real_time_quotation", "600036.SH"),
        ("工商银行成交额", "quote_realtime", "/real_time_quotation", "601398.SH"),
        ("迈瑞医疗今日行情", "quote_realtime", "/real_time_quotation", "300760.SZ"),
        ("查一下600519行情", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("600519行情", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("sh600519行情", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("300750.SZ最新价", "quote_realtime", "/real_time_quotation", "300750.SZ"),
        ("看下宁德时代近一个月走势", "quote_history", "/cmd_history_quotation", "300750.SZ"),
        ("中芯国际近一周走势", "quote_history", "/cmd_history_quotation", "688981.SH"),
        ("药明康德 2026-04-01 到 2026-04-20 走势", "quote_history", "/cmd_history_quotation", "603259.SH"),
        ("比亚迪近半年K线", "quote_history", "/cmd_history_quotation", "002594.SZ"),
        ("东方财富近一年历史行情", "quote_history", "/cmd_history_quotation", "300059.SZ"),
    ]

    for query, intent, endpoint, symbol in cases:
        plan = build_route_plan(
            query,
            entity_lookup=exact_common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == intent, query
        assert plan.endpoint == endpoint, query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.payload["codes"] == symbol, query


def test_index_query_matrix_routes_single_indices_to_market_snapshot():
    cases = [
        ("沪深300现在怎么样", "000300.SH", "沪深300"),
        ("创业板指行情", "399006.SZ", "创业板指"),
        ("上证指数现在多少", "000001.SH", "上证指数"),
        ("深证成指行情", "399001.SZ", "深证成指"),
        ("上证50行情", "000016.SH", "上证50"),
        ("科创50行情", "000688.SH", "科创50"),
        ("中证500指数", "000905.SH", "中证500"),
        ("中证1000现在怎么样", "000852.SH", "中证1000"),
        ("北证50行情", "899050.BJ", "北证50"),
        ("000300.SH行情", "000300.SH", "沪深300"),
    ]

    for query, symbol, name in cases:
        plan = build_route_plan(
            query,
            entity_lookup=lambda _: None,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "market_snapshot", query
        assert plan.endpoint == "/real_time_quotation", query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.entity.name == name, query
        assert plan.payload["codes"] == symbol, query


def test_financial_and_profile_queries_resolve_chinese_name_before_smart_pick():
    cases = [
        ("宁德时代市盈率和总市值是多少", "generic_smart_query", "300750.SZ"),
        ("贵州茅台近三年营收和毛利率", "generic_smart_query", "600519.SH"),
        ("招商银行roe和资产负债率", "generic_smart_query", "600036.SH"),
        ("工商银行2025年营业收入", "generic_smart_query", "601398.SH"),
        ("迈瑞医疗主营业务是什么", "entity_profile", "300760.SZ"),
        ("药明康德属于什么行业", "entity_profile", "603259.SH"),
    ]

    for query, intent, symbol in cases:
        plan = build_route_plan(
            query,
            entity_lookup=exact_common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == intent, query
        assert plan.endpoint == "/smart_stock_picking", query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.payload["searchtype"] == "stock", query


def test_common_a_share_question_matrix_preserves_original_natural_language():
    cases = [
        ("贵州茅台2025年年报", "600519.SH"),
        ("宁德时代2026年一季报", "300750.SZ"),
        ("比亚迪最近公告和分红", "002594.SZ"),
        ("中国平安龙虎榜和大宗交易", "601318.SH"),
        ("中芯国际融资余额和北向持股", "688981.SH"),
        ("药明康德十大股东和机构持仓", "603259.SH"),
        ("迈瑞医疗限售解禁安排", "300760.SZ"),
        ("东方财富所属概念板块", "300059.SZ"),
        ("今天有哪些股票停牌复牌", None),
        ("明天A股有哪些新股申购", None),
        ("半导体板块研报评级", None),
        ("新能源车产业链市盈率低于30的股票", None),
    ]

    for query, symbol in cases:
        plan = build_route_plan(
            query,
            entity_lookup=exact_common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query", query
        assert plan.endpoint == "/smart_stock_picking", query
        assert plan.payload == {
            "searchstring": query,
            "searchtype": "stock",
        }, query
        if symbol is not None:
            assert plan.entity is not None, query
            assert plan.entity.symbol == symbol, query


def test_extreme_punctuation_and_symbol_formats_still_route_precisely():
    cases = [
        ("请问：贵州茅台，最新价是多少？", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("麻烦帮我看一下【宁德时代】现在股价", "quote_realtime", "/real_time_quotation", "300750.SZ"),
        ("给我查下「比亚迪」行情", "quote_realtime", "/real_time_quotation", "002594.SZ"),
        ("中国平安!!!现在!!!股价???", "quote_realtime", "/real_time_quotation", "601318.SH"),
        ("招商银行（600036）现在行情", "quote_realtime", "/real_time_quotation", "600036.SH"),
        ("600519.SH最新价", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("SH600519最新价", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("sz300750走势", "quote_history", "/cmd_history_quotation", "300750.SZ"),
        ("688981.SH近5天走势", "quote_history", "/cmd_history_quotation", "688981.SH"),
        ("835185行情", "quote_realtime", "/real_time_quotation", "835185.BJ"),
        ("510300行情", "quote_realtime", "/real_time_quotation", "510300.SH"),
        ("159915行情", "quote_realtime", "/real_time_quotation", "159915.SZ"),
    ]

    for query, intent, endpoint, symbol in cases:
        plan = build_route_plan(
            query,
            entity_lookup=exact_common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == intent, query
        assert plan.endpoint == endpoint, query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.payload["codes"] == symbol, query


def test_extreme_index_aliases_and_suffix_codes_route_to_market_snapshot():
    cases = [
        ("bj899050行情", "899050.BJ", "北证50"),
        ("000300sh行情", "000300.SH", "沪深300"),
        ("创业板指数现在呢", "399006.SZ", "创业板指"),
        ("科创板50现在多少", "000688.SH", "科创50"),
        ("HS300行情", "000300.SH", "沪深300"),
        ("sz50行情", "000016.SH", "上证50"),
        ("zz500行情", "000905.SH", "中证500"),
        ("zz1000行情", "000852.SH", "中证1000"),
    ]

    for query, symbol, name in cases:
        plan = build_route_plan(
            query,
            entity_lookup=lambda _: None,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "market_snapshot", query
        assert plan.endpoint == "/real_time_quotation", query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.entity.name == name, query
        assert plan.payload["codes"] == symbol, query


def test_extreme_report_holding_and_capital_terms_resolve_entity_and_preserve_query():
    cases = [
        ("贵州茅台2026年一季度报告", "600519.SH"),
        ("宁德时代2026年三季度报告", "300750.SZ"),
        ("比亚迪2025年度报告", "002594.SZ"),
        ("中芯国际半年报摘要", "688981.SH"),
        ("药明康德十大流通股东情况", "603259.SH"),
        ("迈瑞医疗机构持仓变化", "300760.SZ"),
        ("东方财富北向资金持股比例", "300059.SZ"),
        ("工商银行分红派息记录", "601398.SH"),
        ("中芯国际解禁时间表", "688981.SH"),
    ]

    for query, symbol in cases:
        plan = build_route_plan(
            query,
            entity_lookup=exact_common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query", query
        assert plan.endpoint == "/smart_stock_picking", query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.payload == {
            "searchstring": query,
            "searchtype": "stock",
        }, query


def test_casual_stock_alias_queries_correct_ifind_lookup_mistakes():
    wrong_entity = ResolvedEntity(
        raw="wrong",
        symbol="000008.SZ",
        name="神州高铁",
        entity_type="stock",
    )
    cases = [
        ("茅台今天涨没涨", "quote_realtime", "/real_time_quotation", "600519.SH"),
        ("宁王今天咋样", "quote_realtime", "/real_time_quotation", "300750.SZ"),
        ("宁德最近跌得多吗", "quote_realtime", "/real_time_quotation", "300750.SZ"),
        ("比亚迪今天红没红", "quote_realtime", "/real_time_quotation", "002594.SZ"),
        ("中芯今天咋样", "quote_realtime", "/real_time_quotation", "688981.SH"),
        ("迈瑞最近走势咋样", "quote_history", "/cmd_history_quotation", "300760.SZ"),
        ("药明今天咋样", "quote_realtime", "/real_time_quotation", "603259.SH"),
        ("东财现在多少钱", "quote_realtime", "/real_time_quotation", "300059.SZ"),
        ("工行现在股价", "quote_realtime", "/real_time_quotation", "601398.SH"),
        ("招行现在多少", "quote_realtime", "/real_time_quotation", "600036.SH"),
        ("平安股价多少了", "quote_realtime", "/real_time_quotation", "601318.SH"),
        ("平安银行股价多少了", "quote_realtime", "/real_time_quotation", "000001.SZ"),
    ]

    for query, intent, endpoint, symbol in cases:
        plan = build_route_plan(
            query,
            entity_lookup=lambda _: wrong_entity,
            today=date(2026, 4, 25),
        )

        assert plan.intent == intent, query
        assert plan.endpoint == endpoint, query
        assert plan.entity is not None, query
        assert plan.entity.symbol == symbol, query
        assert plan.payload["codes"] == symbol, query


def test_casual_smart_queries_are_rewritten_to_ifind_friendly_terms():
    cases = [
        ("茅台公告有啥", "贵州茅台最近公告"),
        ("宁德有啥研报", "宁德时代研报"),
        ("招行分红怎么样", "招商银行分红记录"),
        ("中芯国际最近有没有啥消息", "中芯国际最近公告"),
        ("东财有啥消息", "东方财富最近公告"),
    ]

    for query, searchstring in cases:
        plan = build_route_plan(
            query,
            entity_lookup=exact_common_a_share_entity_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query", query
        assert plan.endpoint == "/smart_stock_picking", query
        assert plan.payload == {
            "searchstring": searchstring,
            "searchtype": "stock",
        }, query
        assert "normalized_casual_query" in (plan.note or ""), query


def test_casual_profile_query_uses_formal_ifind_wording():
    plan = build_route_plan(
        "茅台干啥的",
        entity_lookup=exact_common_a_share_entity_lookup,
        today=date(2026, 4, 25),
    )

    assert plan.intent == "entity_profile"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.entity is not None
    assert plan.entity.symbol == "600519.SH"
    assert plan.payload == {
        "searchstring": "贵州茅台主营业务是什么",
        "searchtype": "stock",
    }


def test_casual_broad_market_queries_do_not_guess_stock_entities():
    queries = [
        "北向今天买啥了",
        "主力买了啥",
        "资金往哪儿流",
        "宁德市有哪些上市公司",
    ]

    def fail_lookup(text: str) -> ResolvedEntity | None:
        raise AssertionError(f"casual broad query should not lookup entity: {text}")

    for query in queries:
        plan = build_route_plan(
            query,
            entity_lookup=fail_lookup,
            today=date(2026, 4, 25),
        )

        assert plan.intent == "generic_smart_query", query
        assert plan.endpoint == "/smart_stock_picking", query
        assert plan.entity is None, query
        expected_searchstring = (
            "北向资金持股增加前十"
            if query == "北向今天买啥了"
            else query
        )
        assert plan.payload == {
            "searchstring": expected_searchstring,
            "searchtype": "stock",
        }, query


def test_casual_trading_calendar_queries_use_ifind_date_sequence():
    queries = [
        "下个交易日是哪天",
        "下一个交易日是什么时候",
        "今天A股休市吗",
        "明天开不开盘",
    ]

    def fail_lookup(text: str) -> ResolvedEntity | None:
        raise AssertionError(f"trading calendar query should not lookup entity: {text}")

    for query in queries:
        plan = build_route_plan(
            query,
            entity_lookup=fail_lookup,
            today=date(2026, 4, 26),
        )

        assert plan.intent == "trading_calendar", query
        assert plan.endpoint == "/date_sequence", query
        assert plan.entity is not None, query
        assert plan.entity.symbol == "000001.SH", query
        assert plan.payload["codes"] == "000001.SH", query
        assert plan.payload["functionpara"] == {"Days": "Tradedays", "Fill": "Omit"}, query
