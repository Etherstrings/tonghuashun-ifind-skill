from __future__ import annotations

import json
from pathlib import Path

from tonghuashun_ifind_skill.models import TokenBundle


class TokenStateStore:
    def __init__(self, path: Path):
        self.path = path

    def save(self, bundle: TokenBundle) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(bundle.to_dict()), encoding="utf-8")

    def load(self) -> TokenBundle | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return TokenBundle.from_dict(payload)
