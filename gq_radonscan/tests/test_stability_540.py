from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from radonscan3.config import Settings
from radonscan3.diagnostics import run_system_self_test
from radonscan3.homeassistant import HomeAssistantClient
from radonscan3.storage import Storage, StorageError
from radonscan3.web import WebServer


def _settings(tmp_path: Path, monkeypatch) -> Settings:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({"data_management_enabled": True}), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("WEB_PORT", "0")
    monkeypatch.setenv("HOME_ASSISTANT_API_URL", "http://127.0.0.1:9/api")
    return Settings.load(options)


def test_room_save_is_idempotent_and_accepts_decimal_comma(tmp_path: Path):
    storage = Storage(tmp_path / "radon.sqlite3")
    first = storage.save_location({"room": "  Arbeitszimmer ", "measurement_height_m": "1,2"})
    repeated = storage.save_location({"room": "Arbeitszimmer", "measurement_height_m": "1.3"})

    assert first["id"] == repeated["id"]
    assert repeated["measurement_height_m"] == 1.3
    assert len(storage.locations()) == 1


def test_room_rename_cannot_duplicate_another_room(tmp_path: Path):
    storage = Storage(tmp_path / "radon.sqlite3")
    first = storage.save_location({"room": "Keller"})
    second = storage.save_location({"room": "Arbeitszimmer"})

    try:
        storage.save_location({"id": second["id"], "room": "KELLER"})
    except StorageError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate room rename was accepted")
    assert storage.location(first["id"])["room"] == "Keller"


def test_room_roundtrip_self_test_leaves_no_records(tmp_path: Path):
    storage = Storage(tmp_path / "radon.sqlite3")
    before = storage.locations()
    result = storage.room_roundtrip_self_test()
    after = storage.locations()

    assert result == {"ok": True, "detail": "insert/read/rollback"}
    assert before == after == []


def test_system_self_test_is_non_destructive_and_actionable(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, monkeypatch)
    storage = Storage(tmp_path / "radon.sqlite3")
    result = run_system_self_test(storage, settings, HomeAssistantClient())

    assert result["status"] in {"ok", "warning"}
    indexed = {item["id"]: item for item in result["items"]}
    assert indexed["database_integrity"]["status"] == "ok"
    assert indexed["room_persistence"]["status"] == "ok"
    assert indexed["report_directory"]["status"] == "ok"
    assert storage.locations() == []


def test_query_fallback_saves_room_when_ingress_drops_body(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, monkeypatch)
    storage = Storage(tmp_path / "radon.sqlite3")
    web = WebServer(settings, storage)
    web.start()
    port = web.server.server_address[1]
    try:
        query = urlencode({"room": "Gästezimmer", "measurement_height_m": "1,4"})
        request = Request(
            f"http://127.0.0.1:{port}/api/locations?{query}",
            data=b"",
            method="POST",
            headers={"X-Radon-Action": web.csrf_token, "Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read())
        assert response.status == 201
        assert payload["item"]["room"] == "Gästezimmer"
        assert payload["item"]["measurement_height_m"] == 1.4
    finally:
        web.stop()


def test_self_test_endpoint_is_protected_post_action(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, monkeypatch)
    storage = Storage(tmp_path / "radon.sqlite3")
    web = WebServer(settings, storage)
    web.start()
    port = web.server.server_address[1]
    try:
        request = Request(
            f"http://127.0.0.1:{port}/api/self-test",
            data=b"{}",
            method="POST",
            headers={"X-Radon-Action": web.csrf_token, "Content-Type": "application/json"},
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read())
        assert response.status == 200
        assert payload["ok"] is True
        assert any(item["id"] == "room_persistence" for item in payload["items"])
    finally:
        web.stop()


def test_urlencoded_room_form_is_accepted(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, monkeypatch)
    storage = Storage(tmp_path / "radon.sqlite3")
    web = WebServer(settings, storage)
    web.start()
    port = web.server.server_address[1]
    try:
        body = urlencode({"room": "Wohnzimmer", "measurement_height_m": "0,85"}).encode("utf-8")
        request = Request(
            f"http://127.0.0.1:{port}/api/locations",
            data=body,
            method="POST",
            headers={
                "X-Radon-Action": web.csrf_token,
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            },
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read())
        assert response.status == 201
        assert payload["item"]["room"] == "Wohnzimmer"
        assert payload["item"]["measurement_height_m"] == 0.85
    finally:
        web.stop()
