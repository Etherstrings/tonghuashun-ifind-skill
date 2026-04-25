import pytest


@pytest.fixture(autouse=True)
def disable_llm_routing_by_default(monkeypatch):
    monkeypatch.setenv("IFIND_ROUTE_LLM_ENABLED", "0")
