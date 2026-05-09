from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tonghuashun_ifind_skill.models import TokenBundle


class TokenStateStore:
    def __init__(self, path: Path):
        self.path = path

    def save(self, bundle: TokenBundle) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as tmp_file:
            json.dump(bundle.to_dict(), tmp_file)
            temp_path = Path(tmp_file.name)
        temp_path.replace(self.path)

    def load(self) -> TokenBundle | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return TokenBundle.from_dict(payload)
        except (OSError, ValueError, TypeError):
            return None
