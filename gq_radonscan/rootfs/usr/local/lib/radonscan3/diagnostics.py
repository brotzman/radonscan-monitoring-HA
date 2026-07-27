from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import tempfile
from typing import Any

from . import __version__
from .config import Settings
from .homeassistant import HomeAssistantClient
from .storage import Storage


def _item(identifier: str, status: str, detail: object = "") -> dict[str, object]:
    return {"id": identifier, "status": status, "detail": str(detail or "")}


def _directory_write_test(directory: Path) -> tuple[bool, str]:
    directory.mkdir(parents=True, exist_ok=True)
    path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".radon-self-test-", dir=directory, delete=False) as handle:
            handle.write(b"radon-monitoring-self-test")
            handle.flush()
            os.fsync(handle.fileno())
            path = Path(handle.name)
        return path.read_bytes() == b"radon-monitoring-self-test", str(directory)
    except OSError as exc:
        return False, str(exc)
    finally:
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def run_system_self_test(
    storage: Storage,
    settings: Settings,
    homeassistant: HomeAssistantClient,
) -> dict[str, Any]:
    """Run non-destructive operational checks used by the System view."""
    items: list[dict[str, object]] = [_item("api", "ok", __version__)]

    try:
        summary = storage.data_summary()
        integrity = str(summary.get("integrity") or "unknown")
        items.append(_item("database_integrity", "ok" if integrity.lower() == "ok" else "error", integrity))
    except Exception as exc:  # pragma: no cover - defensive boundary
        items.append(_item("database_integrity", "error", exc))

    try:
        room_check = storage.room_roundtrip_self_test()
        items.append(_item("room_persistence", "ok" if room_check.get("ok") else "error", room_check.get("detail")))
    except Exception as exc:  # pragma: no cover - defensive boundary
        items.append(_item("room_persistence", "error", exc))

    reports_ok, reports_detail = _directory_write_test(storage.reports_dir)
    items.append(_item("report_directory", "ok" if reports_ok else "error", reports_detail))

    runtime = storage.runtime_all()
    connection = runtime.get("connection") if isinstance(runtime.get("connection"), dict) else {}
    mqtt = runtime.get("mqtt") if isinstance(runtime.get("mqtt"), dict) else {}
    items.append(
        _item(
            "device_connection",
            "ok" if bool(connection.get("connected")) else "warning",
            connection.get("status") or connection.get("error") or "disconnected",
        )
    )
    items.append(
        _item(
            "mqtt_connection",
            "ok" if bool(mqtt.get("connected")) else "warning",
            mqtt.get("host") or mqtt.get("error") or "disconnected",
        )
    )

    ha_status = homeassistant.status()
    items.append(
        _item(
            "homeassistant_connection",
            "ok" if bool(ha_status.get("connected")) else "warning",
            ha_status.get("version") or ha_status.get("error") or "disconnected",
        )
    )

    statuses = {str(item["status"]) for item in items}
    overall = "error" if "error" in statuses else "warning" if "warning" in statuses else "ok"
    return {
        "status": overall,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": __version__,
        "platform": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "settings": {
            "web_port": settings.web_port,
            "data_management_enabled": settings.data_management_enabled,
        },
        "items": items,
    }
