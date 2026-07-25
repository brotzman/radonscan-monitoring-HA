from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "rootfs" / "usr" / "local" / "lib"
sys.path.insert(0, str(ROOT))

from radonscan3.homeassistant import HomeAssistantClient


def test_long_lived_token_uses_direct_core_url(monkeypatch):
    monkeypatch.delenv("HOME_ASSISTANT_API_URL", raising=False)
    client = HomeAssistantClient("secret-token")
    assert client.base_url == "http://homeassistant:8123/api"
    assert client.token_source == "homeassistant_access_token"


def test_supervisor_token_uses_supervisor_proxy(monkeypatch):
    monkeypatch.delenv("HOME_ASSISTANT_API_URL", raising=False)
    monkeypatch.setenv("SUPERVISOR_TOKEN", "supervisor-token")
    client = HomeAssistantClient("")
    assert client.base_url == "http://supervisor/core/api"
    assert client.token_source == "supervisor_token"


def test_purge_payload_uses_lists_and_globs(monkeypatch):
    client = HomeAssistantClient("secret-token")
    captured = {}

    def fake_request(method, path, payload=None):
        captured.update(method=method, path=path, payload=payload)
        return [{"context": {"id": "abc"}}]

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.purge_entities(
        ["sensor.gq_radonscan_radon", "sensor.gq_radonscan_radon"],
        0,
        ["sensor.gq_radonscan_*"],
    )
    assert captured["method"] == "POST"
    assert captured["path"] == "services/recorder/purge_entities"
    assert captured["payload"] == {
        "keep_days": 0,
        "entity_id": ["sensor.gq_radonscan_radon"],
        "entity_globs": ["sensor.gq_radonscan_*"],
    }
    assert result["requested"] is True


def test_obsolete_selection_ui_removed():
    static = Path(__file__).resolve().parents[1] / "rootfs" / "usr" / "local" / "lib" / "radonscan3" / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    js = (static / "app.js").read_text(encoding="utf-8")
    assert "haEntityList" not in html
    assert "loadHaEntities" not in html
    assert "loadHaEntities" not in js
    assert 'id="purgeHaHistory"' in html
