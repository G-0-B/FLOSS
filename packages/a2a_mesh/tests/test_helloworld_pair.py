"""Spec-minimum A2A pair: card GET then SendMessage."""

from __future__ import annotations

import threading
import time

import httpx
import pytest

from packages.a2a_mesh.client import send_hello
from packages.a2a_mesh.helloworld import serve_helloworld

HOST, PORT = "127.0.0.1", 19999


def test_agent_card_is_served_at_well_known():
    t = threading.Thread(
        target=serve_helloworld, kwargs={"host": HOST, "port": PORT}, daemon=True
    )
    t.start()
    time.sleep(0.4)
    r = httpx.get(f"http://{HOST}:{PORT}/.well-known/agent-card.json", timeout=5)
    assert r.status_code == 200
    card = r.json()
    assert "name" in card
    assert "supportedInterfaces" in card or "url" in card


def test_send_hello_round_trips():
    t = threading.Thread(
        target=serve_helloworld, kwargs={"host": HOST, "port": PORT}, daemon=True
    )
    t.start()
    time.sleep(0.4)
    text = send_hello(f"http://{HOST}:{PORT}", "ping")
    assert isinstance(text, str)
    assert len(text) > 0
