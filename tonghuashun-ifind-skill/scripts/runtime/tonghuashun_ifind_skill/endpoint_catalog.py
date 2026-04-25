from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    endpoint: str
    category: str
    description: str
    example_payload: dict[str, object]
    requires_ifind_auth: bool = True
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "category": self.category,
            "description": self.description,
            "example_payload": self.example_payload,
            "requires_ifind_auth": self.requires_ifind_auth,
            "notes": list(self.notes),
        }


_ENDPOINT_SPECS = {
    "basic_data": EndpointSpec(
        name="basic_data",
        endpoint="/basic_data_service",
        category="core_api",
        description="基础指标查询，适合直接按代码和指标名取数。",
        example_payload={
            "codes": "300750.SZ",
            "indicators": "ths_close_price_stock",
        },
    ),
    "smart_pick": EndpointSpec(
        name="smart_pick",
        endpoint="/smart_stock_picking",
        category="core_api",
        description="自然语言选股与金融问答透传接口，涨停、榜单、画像、资金流都基于它。",
        example_payload={
            "searchstring": "今天的A股涨停数据",
            "searchtype": "stock",
        },
        notes=(
            "所有数据来自 iFinD；使用前必须完成鉴权。",
            "涨停、榜单、画像和资金流都通过 iFinD smart_stock_picking 透传。",
        ),
    ),
    "report_query": EndpointSpec(
        name="report_query",
        endpoint="/report_query",
        category="core_api",
        description="研报或报告类查询透传接口。",
        example_payload={"codes": "300750.SZ"},
    ),
    "date_sequence": EndpointSpec(
        name="date_sequence",
        endpoint="/date_sequence",
        category="core_api",
        description="日期序列、交易日历等时间轴能力透传接口。",
        example_payload={
            "codes": "000001.SH",
            "startdate": "2026-04-01",
            "enddate": "2026-04-30",
            "functionpara": {"Days": "Tradedays", "Fill": "Omit"},
            "indipara": [
                {
                    "indicator": "ths_close_price_stock",
                    "indiparams": ["", "100", ""],
                }
            ],
        },
    ),
    "real_time_quote": EndpointSpec(
        name="real_time_quote",
        endpoint="/real_time_quotation",
        category="market_data",
        description="实时行情原始接口，适合单股或指数快照。",
        example_payload={
            "codes": "600519.SH,000300.SH",
            "indicators": (
                "open,high,low,latest,changeRatio,change,preClose,volume,"
                "amount,turnoverRatio,volumeRatio,amplitude,pb"
            ),
        },
        notes=("所有行情数据来自 iFinD；不再回退到公开行情源。",),
    ),
    "history_quote": EndpointSpec(
        name="history_quote",
        endpoint="/cmd_history_quotation",
        category="market_data",
        description="历史行情原始接口，适合日线区间查询。",
        example_payload={
            "codes": "600004.SH",
            "indicators": "open,close,high,low,volume",
            "startdate": "2026-04-21",
            "enddate": "2026-04-21",
        },
        notes=("所有历史行情数据来自 iFinD；不再回退到公开行情源。",),
    ),
    "limit_up_screen": EndpointSpec(
        name="limit_up_screen",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="涨停池能力别名；推荐优先用 smart-query。",
        example_payload={
            "searchstring": "今天的A股涨停数据",
            "searchtype": "stock",
        },
        notes=("所有涨停数据来自 iFinD smart_stock_picking。",),
    ),
    "leaderboard_screen": EndpointSpec(
        name="leaderboard_screen",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="榜单能力别名；适合成交额榜、涨跌幅榜、换手率榜、振幅榜、量比榜。",
        example_payload={
            "searchstring": "A股成交额榜前十",
            "searchtype": "stock",
        },
        notes=("所有榜单数据来自 iFinD smart_stock_picking。",),
    ),
    "fundamental_basic": EndpointSpec(
        name="fundamental_basic",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="基本面能力别名；推荐优先用 smart-query 或 fundamental-basic。",
        example_payload={
            "searchstring": "宁德时代基本面",
            "searchtype": "stock",
        },
        notes=("所有基本面数据来自 iFinD smart_stock_picking。",),
    ),
    "entity_profile": EndpointSpec(
        name="entity_profile",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="公司简介、主营业务等画像能力别名。",
        example_payload={
            "searchstring": "贵州茅台主营业务是什么",
            "searchtype": "stock",
        },
        notes=("所有画像数据来自 iFinD smart_stock_picking。",),
    ),
    "capital_flow": EndpointSpec(
        name="capital_flow",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="资金流问法能力别名。",
        example_payload={
            "searchstring": "今天主力资金流入前十",
            "searchtype": "stock",
        },
        notes=("所有资金流数据来自 iFinD smart_stock_picking。",),
    ),
    "a_share_common_query": EndpointSpec(
        name="a_share_common_query",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="A 股用户常见自然语言查询入口；覆盖公告、研报、龙虎榜、两融、北向、股东、持仓、分红、解禁、停复牌、概念板块、新股和交易日等问法。",
        example_payload={
            "searchstring": "贵州茅台最近分红、十大股东和北向持股情况",
            "searchtype": "stock",
        },
        notes=(
            "这些问法保留用户原始自然语言交给 iFinD smart_stock_picking。",
            "如果 iFinD 返回权限不足或无法处理，直接反馈 iFinD 失败，不切换公开源。",
        ),
    ),
    "generic_smart_query": EndpointSpec(
        name="generic_smart_query",
        endpoint="/smart_stock_picking",
        category="routed_capability",
        description="自然语言泛化查询入口；当本地规则没有稳定命中特定能力时，将用户原问题交给 iFinD smart_stock_picking。",
        example_payload={
            "searchstring": "筛一下新能源车产业链里市盈率低于30且近一个月放量的股票",
            "searchtype": "stock",
        },
        notes=("这是 smart-query 的自然语言兜底入口，但数据仍然只来自 iFinD。",),
    ),
}


def list_endpoint_specs() -> list[EndpointSpec]:
    return [
        _ENDPOINT_SPECS[name]
        for name in sorted(_ENDPOINT_SPECS.keys())
    ]


def get_endpoint_spec(name: str) -> EndpointSpec:
    normalized_name = name.strip().lower()
    try:
        return _ENDPOINT_SPECS[normalized_name]
    except KeyError as exc:
        supported = ", ".join(sorted(_ENDPOINT_SPECS.keys()))
        raise ValueError(
            f"unknown endpoint name: {name}. supported names: {supported}"
        ) from exc
