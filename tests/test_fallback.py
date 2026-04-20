from __future__ import annotations

from datetime import date

from tonghuashun_ifind_skill.routing import RoutePlan
from tonghuashun_ifind_skill.fallback import TencentStockFallbackClient


class FakeResponse:
    def __init__(
        self,
        *,
        content: bytes | None = None,
        json_payload: object | None = None,
        status_code: int = 200,
    ) -> None:
        self.content = content or b""
        self._json_payload = json_payload
        self.status_code = status_code

    def json(self) -> object:
        if self._json_payload is None:
            raise ValueError("missing json payload")
        return self._json_payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http error {self.status_code}")


class FakeSession:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []
        self._responses: list[FakeResponse] = []

    def queue_response(self, response: FakeResponse) -> None:
        self._responses.append(response)

    def get(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
        timeout: float,
    ) -> FakeResponse:
        self.requests.append(
            {
                "url": url,
                "params": params,
                "timeout": timeout,
            }
        )
        if not self._responses:
            raise AssertionError("no queued response")
        return self._responses.pop(0)


def test_tencent_search_entity_parses_stock_match() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            content='v_hint="sh~600519~\\u8d35\\u5dde\\u8305\\u53f0~gzmt~GP-A"'.encode("utf-8"),
        )
    )
    client = TencentStockFallbackClient(session=session)

    entity = client.search_entity("贵州茅台")

    assert entity is not None
    assert entity.symbol == "600519.SH"
    assert entity.name == "贵州茅台"
    assert entity.entity_type == "stock"


def test_tencent_quote_realtime_parses_quote_payload() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            content=(
                'v_sh600519="1~贵州茅台~600519~1462.84~1467.50~1467.45~24513~10823~13690~1462.84~6~1462.83~1~1462.82~1~1462.80~6~1462.79~1~1463.00~2~1463.49~8~1463.50~4~1463.53~8~1463.60~3~~20260416161427~-4.66~-0.32~1477.41~1460.00~";'
            ).encode("gbk"),
        )
    )
    client = TencentStockFallbackClient(session=session)

    result = client.fetch_realtime(["600519.SH"])

    assert result["provider"]["name"] == "tencent_finance"
    assert result["quotes"][0]["symbol"] == "600519.SH"
    assert result["quotes"][0]["name"] == "贵州茅台"
    assert result["quotes"][0]["latest"] == 1462.84
    assert result["quotes"][0]["change"] == -4.66
    assert result["quotes"][0]["change_ratio"] == -0.32


def test_tencent_quote_history_parses_kline_payload() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            content=(
                'kline_dayqfq={"code":0,"msg":"","data":{"sh600519":{"day":[["2026-04-15","1444.980","1467.500","1470.790","1442.000","34553.000"],["2026-04-16","1467.450","1462.840","1477.410","1460.000","24513.000"]]}}}'
            ).encode("utf-8"),
        )
    )
    client = TencentStockFallbackClient(session=session)

    result = client.fetch_history(
        symbol="600519.SH",
        start_date="2026-04-15",
        end_date="2026-04-16",
    )

    assert result["provider"]["name"] == "tencent_finance"
    assert result["symbol"] == "600519.SH"
    assert result["candles"][0]["date"] == "2026-04-15"
    assert result["candles"][1]["close"] == 1462.84


def test_eastmoney_limit_up_pool_parses_public_payload() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            json_payload={
                "rc": 0,
                "data": {
                    "qdate": 20260420,
                    "pool": [
                        {
                            "c": "002843",
                            "m": 0,
                            "n": "泰嘉股份",
                            "p": 27980,
                            "zdp": 9.98427677154541,
                            "lbc": 1,
                            "fbt": 92500,
                            "lbt": 92500,
                            "hybk": "通用设备",
                            "fund": 117854641,
                            "zbc": 0,
                            "zttj": {"days": 1, "ct": 1},
                        }
                    ],
                },
            }
        )
    )
    client = TencentStockFallbackClient(session=session)

    result = client.fetch_limit_up_pool(trade_date=date(2026, 4, 20))

    assert result["provider"]["name"] == "eastmoney"
    assert result["trade_date"] == "2026-04-20"
    assert result["limit_up_stocks"][0]["symbol"] == "002843.SZ"
    assert result["limit_up_stocks"][0]["name"] == "泰嘉股份"
    assert result["limit_up_stocks"][0]["latest"] == 27.98
    assert result["limit_up_stocks"][0]["board_count"] == 1


def test_execute_plan_supports_limit_up_screen() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            json_payload={
                "rc": 0,
                "data": {
                    "qdate": 20260420,
                    "pool": [{"c": "002843", "m": 0, "n": "泰嘉股份", "p": 27980}],
                },
            }
        )
    )
    client = TencentStockFallbackClient(session=session)

    result = client.execute_plan(
        RoutePlan(
            intent="limit_up_screen",
            endpoint="/smart_stock_picking",
            payload={"searchstring": "今天的A股涨停数据", "searchtype": "stock"},
            entity=None,
            note=None,
        )
    )

    assert result["provider"]["name"] == "eastmoney"
    assert result["limit_up_stocks"][0]["symbol"] == "002843.SZ"


def test_eastmoney_leaderboard_parses_turnover_ranking_payload() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            json_payload={
                "rc": 0,
                "data": {
                    "total": 2,
                    "diff": [
                        {
                            "f12": "600519",
                            "f14": "贵州茅台",
                            "f2": 1462.84,
                            "f3": -0.32,
                            "f6": 3456789012.0,
                            "f8": 0.83,
                            "f10": 1.27,
                        },
                        {
                            "f12": "300750",
                            "f14": "宁德时代",
                            "f2": 201.22,
                            "f3": 2.13,
                            "f6": 2987654321.0,
                            "f8": 1.12,
                            "f10": 1.56,
                        },
                    ],
                },
            }
        )
    )
    client = TencentStockFallbackClient(session=session)

    result = client.fetch_leaderboard(rank_type="turnover", limit=2)

    assert result["provider"]["name"] == "eastmoney"
    assert result["leaderboard_type"] == "turnover"
    assert result["items"][0]["symbol"] == "600519.SH"
    assert result["items"][0]["name"] == "贵州茅台"
    assert result["items"][0]["turnover"] == 3456789012.0


def test_execute_plan_supports_leaderboard_screen() -> None:
    session = FakeSession()
    session.queue_response(
        FakeResponse(
            json_payload={
                "rc": 0,
                "data": {
                    "total": 1,
                    "diff": [{"f12": "600519", "f14": "贵州茅台", "f2": 1462.84, "f3": -0.32, "f6": 3456789012.0}],
                },
            }
        )
    )
    client = TencentStockFallbackClient(session=session)

    result = client.execute_plan(
        RoutePlan(
            intent="leaderboard_screen",
            endpoint="/smart_stock_picking",
            payload={
                "searchstring": "A股成交额榜前十",
                "searchtype": "stock",
                "fallback_type": "turnover",
                "limit": 10,
            },
            entity=None,
            note=None,
        )
    )

    assert result["provider"]["name"] == "eastmoney"
    assert result["leaderboard_type"] == "turnover"
    assert result["items"][0]["symbol"] == "600519.SH"
