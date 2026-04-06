import pytest

from tonghuashun_ifind_skill.client import IFindClient


class FakeResponse:
    def __init__(self, payload: object, *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> object:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http error {self.status_code}")


class FakeSession:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []
        self._responses: list[FakeResponse] = []

    def queue_response(self, payload: object, *, status_code: int = 200) -> None:
        self._responses.append(FakeResponse(payload, status_code=status_code))

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
        if self._responses:
            return self._responses.pop(0)
        return FakeResponse({"errorcode": 0, "errmsg": "OK", "data": {}})


@pytest.fixture
def fake_session() -> FakeSession:
    return FakeSession()


def test_api_call_posts_to_requested_endpoint(fake_session: FakeSession) -> None:
    client = IFindClient(
        base_url="https://quantapi.51ifind.com/api/v1",
        session=fake_session,
    )
    result = client.api_call(
        endpoint="/basic_data_service",
        payload={"codes": "300750.SZ"},
        access_token="access-demo",
        token_source="cache",
    )
    assert result["ok"] is True
    assert result["endpoint"] == "/basic_data_service"


@pytest.mark.parametrize(
    ("method_name", "endpoint"),
    [
        ("basic_data", "/basic_data_service"),
        ("smart_stock_picking", "/smart_stock_picking"),
        ("report_query", "/report_query"),
        ("date_sequence", "/date_sequence"),
    ],
)
def test_wrapper_methods_forward_endpoint(
    fake_session: FakeSession,
    method_name: str,
    endpoint: str,
) -> None:
    client = IFindClient(
        base_url="https://quantapi.51ifind.com/api/v1",
        session=fake_session,
    )
    fake_session.queue_response({"errorcode": 0, "errmsg": "OK", "data": {"k": 1}})

    result = getattr(client, method_name)(
        payload={"codes": "300750.SZ"},
        access_token="access-demo",
        token_source="cache",
    )

    assert result["endpoint"] == endpoint
    assert fake_session.requests[-1]["url"] == (
        "https://quantapi.51ifind.com/api/v1" + endpoint
    )


def test_api_call_preserves_ifind_business_error(fake_session: FakeSession) -> None:
    client = IFindClient(
        base_url="https://quantapi.51ifind.com/api/v1",
        session=fake_session,
    )
    fake_session.queue_response({"errorcode": 1001, "errmsg": "bad param"})

    result = client.api_call(
        endpoint="/basic_data_service",
        payload={"codes": "300750.SZ"},
        access_token="access-demo",
        token_source="cache",
    )

    assert result["ok"] is False
    assert result["error"]["errorcode"] == 1001
    assert result["error"]["errmsg"] == "bad param"
