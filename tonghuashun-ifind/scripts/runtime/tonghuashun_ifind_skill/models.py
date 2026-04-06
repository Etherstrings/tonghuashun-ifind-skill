from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class TokenBundle:
    access_token: str
    refresh_token: str
    expires_at: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "TokenBundle":
        if not isinstance(data, dict):
            raise ValueError("token state must be a JSON object")

        access_token = cls._require_text(data, "access_token")
        refresh_token = cls._require_text(data, "refresh_token")
        expires_at = data.get("expires_at")

        if expires_at is not None and not isinstance(expires_at, str):
            raise ValueError("expires_at must be a string or null")

        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

    def is_stale(self, *, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return True
        current_time = self._normalize_datetime(now or datetime.now(UTC))
        try:
            return current_time >= self.expires_at_datetime
        except ValueError:
            return True

    @property
    def expires_at_datetime(self) -> datetime:
        if self.expires_at is None:
            raise ValueError("expires_at is not set")
        try:
            parsed = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("expires_at must be a valid ISO 8601 datetime") from exc
        return self._normalize_datetime(parsed)

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _require_text(data: dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value


@dataclass(slots=True)
class ErrorPayload:
    type: str
    message: str
    errorcode: int | str | None = None
    errmsg: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": self.type,
            "message": self.message,
        }
        if self.errorcode is not None:
            payload["errorcode"] = self.errorcode
        if self.errmsg is not None:
            payload["errmsg"] = self.errmsg
        return payload


@dataclass(slots=True)
class ResponseMeta:
    timestamp: str

    def to_dict(self) -> dict[str, str]:
        return {"timestamp": self.timestamp}


@dataclass(slots=True)
class ResponseEnvelope:
    ok: bool
    endpoint: str
    token_source: str
    data: object | None
    error: ErrorPayload | None
    meta: ResponseMeta

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "endpoint": self.endpoint,
            "token_source": self.token_source,
            "data": self.data,
            "error": None if self.error is None else self.error.to_dict(),
            "meta": self.meta.to_dict(),
        }


def format_timestamp(now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    else:
        current = current.astimezone(UTC)
    current = current.replace(microsecond=0)
    return current.isoformat().replace("+00:00", "Z")
