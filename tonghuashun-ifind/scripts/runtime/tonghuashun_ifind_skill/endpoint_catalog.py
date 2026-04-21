from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    endpoint: str
    category: str
    description: str
    example_payload: dict[str, object]
    supports_public_fallback: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "category": self.category,
            "description": self.description,
            "example_payload": self.example_payload,
            "supports_public_fallback": self.supports_public_fallback,
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
        supports_public_fallback=True,
        notes=(
            "涨停和榜单问法有免费公开源兜底。",
            "画像和资金流当前没有稳定公开源兜底。",
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
            "startdate": "2026-04-01",
            "enddate": "2026-04-30",
        },
    ),
    "real_time_quote": EndpointSpec(
        name="real_time_quote",
        endpoint="/real_time_quotation",
        category="market_data",
        description="实时行情原始接口，适合单股或指数快照。",
        example_payload={"codes": "600519.SH,000300.SH"},
        supports_public_fallback=True,
        notes=("免费兜底使用腾讯财经公开行情。",),
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
        supports_public_fallback=True,
        notes=("免费兜底使用腾讯财经历史行情。",),
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
        supports_public_fallback=True,
        notes=("免费兜底使用东方财富涨停池。",),
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
        supports_public_fallback=True,
        notes=("免费兜底使用东方财富排行榜。",),
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
        notes=("当前没有稳定公开源兜底。",),
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
        notes=("当前没有稳定公开源兜底。",),
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
        notes=("当前没有稳定公开源兜底。",),
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
