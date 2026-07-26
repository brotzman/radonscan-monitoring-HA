from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from radonscan3.device import ScanResult
from radonscan3.homeassistant import HomeAssistantClient
from radonscan3.operations import DataManagementOperations, RADON_ENTITY_GLOBS
from radonscan3.polling import update_connection_runtime
from radonscan3.report_utils import peak_preserving_downsample
from radonscan3.security import redact_sensitive, safe_error_message
from radonscan3.storage import Storage


def test_sensitive_values_are_redacted_recursively():
    secret = "very-secret-admin-token"
    payload = {
        "homeassistant_access_token": secret,
        "nested": {"Authorization": f"Bearer {secret}", "device_id": "local-radonscan-1"},
        "gmcmap_account_id": "123456",
        "message": f"upstream echoed {secret}",
    }
    redacted = redact_sensitive(payload, extra_secrets=(secret,))
    assert secret not in str(redacted)
    assert redacted["homeassistant_access_token"] == "<redacted>"
    assert redacted["gmcmap_account_id"] == "<redacted>"
    assert redacted["nested"]["device_id"] == "local-radonscan-1"
    assert redacted["nested"]["Authorization"] == "<redacted>"
    assert secret not in safe_error_message(f"Bearer {secret}", secret)


def test_history_summary_counts_rows_and_chunks(monkeypatch):
    client = HomeAssistantClient("secret-token")
    calls = []

    def fake_request(method, path, payload=None):
        calls.append((method, path, payload))
        return [
            [{"entity_id": "sensor.gq_radonscan_radon", "state": "10"}, {"state": "11"}],
            [{"entity_id": "sensor.radon_monitoring_24h", "state": "9"}],
        ]

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.history_summary(
        ["sensor.gq_radonscan_radon", "sensor.radon_monitoring_24h"],
        start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end=datetime(2025, 1, 2, tzinfo=timezone.utc),
        chunk_size=20,
    )
    assert result["verified"] is False
    assert result["remaining_rows"] == 3
    assert set(result["entities_with_history"]) == {
        "sensor.gq_radonscan_radon",
        "sensor.radon_monitoring_24h",
    }
    assert calls and calls[0][0] == "GET"
    assert "history/period/" in calls[0][1]
    assert "filter_entity_id=" in calls[0][1]
    assert "minimal_response" in calls[0][1]


def test_operations_purge_and_verification_are_auditable(tmp_path: Path):
    storage = Storage(tmp_path / "radon.sqlite3")

    class FakeHomeAssistant:
        def radon_entities(self):
            return [{"entity_id": "sensor.gq_radonscan_radon"}]

        def purge_entities(self, entity_ids, keep_days, entity_globs):
            assert entity_ids == ["sensor.gq_radonscan_radon"]
            assert keep_days == 0
            assert tuple(entity_globs) == RADON_ENTITY_GLOBS
            return {
                "requested": True,
                "entity_ids": entity_ids,
                "entity_globs": entity_globs,
                "keep_days": keep_days,
                "authentication": "homeassistant_access_token",
                "requested_at": "2026-07-26T00:00:00+00:00",
            }

        def history_summary(self, entity_ids):
            assert entity_ids == ["sensor.gq_radonscan_radon"]
            return {
                "verified": True,
                "status": "complete",
                "remaining_rows": 0,
                "checked_at": "2026-07-26T00:05:00+00:00",
            }

    operations = DataManagementOperations(storage, FakeHomeAssistant())
    purge = operations.purge_home_assistant_history("Tester")
    assert purge["verification"] == "pending"
    assert purge["detected_entities"] == 1
    persisted = storage.get_runtime("homeassistant_purge_last", {})
    assert persisted["operation_id"] == purge["operation_id"]

    verification = operations.verify_home_assistant_history("Tester")
    assert verification["verified"] is True
    assert verification["checked_entities"] == 1
    actions = [entry["action"] for entry in storage.audit_entries(20)]
    assert "homeassistant_purge_all" in actions
    assert "homeassistant_purge_verify" in actions


def test_usb_disconnect_and_reconnect_status_transitions(tmp_path: Path):
    storage = Storage(tmp_path / "radon.sqlite3")
    now = datetime(2026, 7, 26, 8, 0, tzinfo=timezone.utc)
    disconnected = ScanResult(False, now, None, None, None, None, None, "no serial ports found", ())
    connected = ScanResult(True, now, "/dev/ttyUSB0", "GQ RadonScan", "RadonScan Re2.02", "ABC", None, None, ("/dev/ttyUSB0",))

    first = update_connection_runtime(storage, disconnected)
    second = update_connection_runtime(storage, connected)
    third = update_connection_runtime(storage, disconnected)
    fourth = update_connection_runtime(storage, connected)

    assert first["status"] == "disconnected"
    assert second["status"] == "connected" and second["error"] is None
    assert third["error"] == "no serial ports found"
    assert fourth["port"] == "/dev/ttyUSB0"
    assert storage.get_runtime("connection")["connected"] is True


def test_peak_preserving_downsample_keeps_endpoints_and_extremes():
    records = [
        {"completed_at": f"2026-01-{index + 1:02d}", "bq_m3": float(index)}
        for index in range(28)
    ]
    records[7]["bq_m3"] = 999.0
    records[19]["bq_m3"] = -20.0
    sampled = peak_preserving_downsample(records, max_points=12)
    values = [row["bq_m3"] for row in sampled]
    assert len(sampled) <= 12
    assert sampled[0] is records[0]
    assert sampled[-1] is records[-1]
    assert 999.0 in values
    assert -20.0 in values
