from __future__ import annotations

from collections.abc import Callable
from datetime import UTC
from datetime import datetime
from typing import Any

from tonghuashun_ifind_skill.models import ErrorPayload
from tonghuashun_ifind_skill.models import ResponseEnvelope
from tonghuashun_ifind_skill.models import ResponseMeta
from tonghuashun_ifind_skill.models import format_timestamp


class IFindClient:
    def __init__(
        self,
        *,
        base_url: str,
        session: Any | None = None,
        timeout: float = 30.0,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session if session is not None else self._default_session()
        self.timeout = timeout
        self._now = now or (lambda: datetime.now(UTC))

    def api_call(
        self,
        endpoint: str,
        payload: dict[str, object],
        access_token: str,
        token_source: str,
    ) -> dict[str, object]:
        normalized_endpoint = self._normalize_endpoint(endpoint)
        url = f"{self.base_url}{normalized_endpoint}"
        headers = {"access_token": access_token}
        timestamp = format_timestamp(self._now())

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except Exception as exc:
            envelope = ResponseEnvelope(
                ok=False,
                endpoint=normalized_endpoint,
                token_source=token_source,
                data=None,
                error=ErrorPayload(type="runtime_failed", message=str(exc)),
                meta=ResponseMeta(timestamp=timestamp),
            )
            return envelope.to_dict()

        status_code = getattr(response, "status_code", 200)
        try:
            body = response.json()
        except Exception as exc:
            error_message = str(exc) if status_code < 400 else f"http error {status_code}"
            envelope = ResponseEnvelope(
                ok=False,
                endpoint=normalized_endpoint,
                token_source=token_source,
                data=None,
                error=ErrorPayload(type="runtime_failed", message=error_message),
                meta=ResponseMeta(timestamp=timestamp),
            )
            return envelope.to_dict()

        error = self._extract_error(body)
        if status_code >= 400:
            if error is None:
                error = ErrorPayload(
                    type="runtime_failed",
                    message=f"http error {status_code}",
                )
            envelope = ResponseEnvelope(
                ok=False,
                endpoint=normalized_endpoint,
                token_source=token_source,
                data=None,
                error=error,
                meta=ResponseMeta(timestamp=timestamp),
            )
            return envelope.to_dict()

        envelope = ResponseEnvelope(
            ok=error is None,
            endpoint=normalized_endpoint,
            token_source=token_source,
            data=None if error is not None else body,
            error=error,
            meta=ResponseMeta(timestamp=timestamp),
        )
        return envelope.to_dict()

    def basic_data(
        self,
        payload: dict[str, object],
        access_token: str,
        token_source: str,
    ) -> dict[str, object]:
        return self.api_call("/basic_data_service", payload, access_token, token_source)

    def smart_stock_picking(
        self,
        payload: dict[str, object],
        access_token: str,
        token_source: str,
    ) -> dict[str, object]:
        return self.api_call(
            "/smart_stock_picking",
            payload,
            access_token,
            token_source,
        )

    def report_query(
        self,
        payload: dict[str, object],
        access_token: str,
        token_source: str,
    ) -> dict[str, object]:
        return self.api_call("/report_query", payload, access_token, token_source)

    def date_sequence(
        self,
        payload: dict[str, object],
        access_token: str,
        token_source: str,
    ) -> dict[str, object]:
        return self.api_call(
            "/date_sequence",
            payload,
            access_token,
            token_source,
        )

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        if not endpoint:
            return "/"
        return endpoint if endpoint.startswith("/") else f"/{endpoint}"

    @staticmethod
    def _default_session() -> Any:
        try:
            import requests
        except ModuleNotFoundError as exc:  # pragma: no cover - fallback for runtime
            raise RuntimeError("requests is required for default sessions") from exc
        return requests.Session()

    @staticmethod
    def _extract_error(payload: object) -> ErrorPayload | None:
        if not isinstance(payload, dict):
            return None
        if "errorcode" not in payload:
            return None
        errorcode = payload.get("errorcode")
        errmsg = payload.get("errmsg")
        if errorcode in (0, "0", None):
            return None
        message = errmsg if isinstance(errmsg, str) else "iFinD business error"
        return ErrorPayload(
            type="api_failed",
            message=message,
            errorcode=errorcode,
            errmsg=errmsg if isinstance(errmsg, str) else None,
        )
