from pathlib import Path

from tonghuashun_ifind_skill.models import TokenBundle
from tonghuashun_ifind_skill.state import TokenStateStore


def test_state_store_round_trips_token_bundle(tmp_path: Path):
    store = TokenStateStore(tmp_path / "tokens.json")
    bundle = TokenBundle(
        access_token="access-demo",
        refresh_token="refresh-demo",
        expires_at="2026-04-06T12:00:00Z",
    )
    store.save(bundle)
    loaded = store.load()
    assert loaded is not None
    assert loaded.access_token == "access-demo"
    assert loaded.refresh_token == "refresh-demo"
