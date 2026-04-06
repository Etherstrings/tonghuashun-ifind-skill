from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime


@dataclass(slots=True)
class TokenBundle:
    access_token: str
    refresh_token: str
    expires_at: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> "TokenBundle":
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data.get("expires_at"),
        )

    def is_stale(self, *, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        current_time = now or datetime.now(UTC)
        return current_time >= self.expires_at_datetime

    @property
    def expires_at_datetime(self) -> datetime:
        if self.expires_at is None:
            raise ValueError("expires_at is not set")
        return datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
