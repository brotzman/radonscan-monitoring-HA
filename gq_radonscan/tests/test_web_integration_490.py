from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

from radonscan3.config import Settings
from radonscan3.storage import Storage
from radonscan3.web import WebServer


def _settings(tmp_path: Path, monkeypatch) -> Settings:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({
        "homeassistant_access_token": "secret-admin-token",
        "gmcmap_account_id": "secret-account",
        "gmcmap_device_id": "secret-device",
        "data_management_enabled": True,
    }))
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("WEB_PORT", "0")
    monkeypatch.setenv("HOME_ASSISTANT_API_URL", "http://127.0.0.1:9/api")
    return Settings.load(options)


def _get(url: str):
    with urlopen(url, timeout=5) as response:
        return response.status, response.headers, response.read()


def _post(url: str, token: str, payload: dict):
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "X-Radon-Action": token},
    )
    with urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read())


def test_real_http_server_serves_all_frontend_modules_and_secure_diagnostics(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, monkeypatch)
    storage = Storage(tmp_path / "radonscan.sqlite3")
    storage.set_runtime("test_credentials", {
        "homeassistant_access_token": "secret-admin-token",
        "gmcmap_account_id": "secret-account",
        "safe_value": "visible",
    })
    web = WebServer(settings, storage)
    web.gmcmap.upload_latest = lambda **kwargs: {"uploaded": True, "trigger": kwargs.get("trigger")}
    web.operations.verify_home_assistant_history = lambda user_name=None: {
        "verified": True, "remaining_rows": 0, "checked_entities": 1, "status": "complete"
    }
    web.start()
    port = web.server.server_address[1]
    base = f"http://127.0.0.1:{port}"
    try:
        for asset in ("core.js", "accessibility.js", "data-management.js", "app.js", "app.css"):
            status, headers, body = _get(f"{base}/assets/{asset}")
            assert status == 200
            assert body
            assert headers["Cache-Control"] == "no-store"

        status, _, body = _get(f"{base}/api/diagnostics")
        text = body.decode()
        assert status == 200
        assert "secret-admin-token" not in text
        assert "secret-account" not in text
        assert "<redacted>" in text
        assert "visible" in text

        status, upload = _post(
            f"{base}/api/gmcmap/upload",
            web.csrf_token,
            {"confirmation": "HOCHLADEN"},
        )
        assert status == 200 and upload["result"]["uploaded"] is True

        status, verify = _post(
            f"{base}/api/homeassistant/verify-purge",
            web.csrf_token,
            {"confirmed": True},
        )
        assert status == 200 and verify["verified"] is True

        # Room metadata remains writable even if Home Assistant Core is
        # temporarily unavailable. No place or building value is copied into
        # the local room record.
        status, saved = _post(
            f"{base}/api/locations",
            web.csrf_token,
            {"room": "Keller", "measurement_height_m": 1.2},
        )
        assert status == 201
        assert saved["item"]["room"] == "Keller"
        assert saved["item"]["measurement_height_m"] == 1.2
        assert saved["item"]["building"] == ""
        assert saved["item"]["homeassistant_location"]["connected"] is False
    finally:
        web.stop()
