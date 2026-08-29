import os
import pytest
import httpx

HERMES = os.environ.get("FLOSS_HERMES_A2A", "http://127.0.0.1:9900")


@pytest.mark.skipif(
    os.environ.get("FLOSS_PROBE_HERMES_A2A") != "1",
    reason="set FLOSS_PROBE_HERMES_A2A=1 when Hermes A2A is running",
)
def test_hermes_serves_agent_card():
    r = httpx.get(f"{HERMES}/.well-known/agent-card.json", timeout=5)
    assert r.status_code == 200
    card = r.json()
    assert "name" in card
