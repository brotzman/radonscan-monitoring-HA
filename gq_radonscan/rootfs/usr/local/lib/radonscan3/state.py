from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import __version__
from .analysis import parse_dt
from .config import Settings
from .storage import Storage


def _pci(value: float | None) -> float | None:
    return None if value is None else round(float(value) / 37.0, 6)


def _status(value: float | None, settings: Settings) -> str:
    if value is None:
        return "unknown"
    if value >= settings.danger_threshold_bq_m3:
        return "danger"
    if value >= settings.warning_threshold_bq_m3:
        return "warning"
    return "normal"


def build_state(storage: Storage, settings: Settings) -> dict[str, Any]:
    latest = storage.latest()
    current_device_id = str(latest.get("device_id")) if latest else None
    device = storage.device(current_device_id) or {}
    runtime = storage.runtime_all()
    connection = runtime.get("connection") or {
        "connected": False,
        "status": "disconnected",
        "error": "not_scanned",
    }
    protocol = runtime.get("protocol") or {}
    mqtt = runtime.get("mqtt") or {"connected": False}
    stats = storage.stats(settings.minimum_data_coverage_percent, current_device_id)
    data_summary = storage.data_summary()

    current_bq = float(latest["bq_m3"]) if latest else None
    completed_at = latest.get("completed_at") if latest else None
    completed_dt = parse_dt(completed_at)
    age_hours = (
        (datetime.now(timezone.utc) - completed_dt).total_seconds() / 3600.0
        if completed_dt else None
    )
    state = {
        "app": {
            "name": "Radon Monitoring",
            "version": __version__,
            "experimental": False,
            "read_only_device": True,
            "subtitle": "Local monitoring for GQ RadonScan devices",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "connection": connection,
        "mqtt": mqtt,
        "device": {
            "device_id": latest.get("device_id") if latest else device.get("device_id"),
            "model": device.get("model"),
            "firmware": device.get("firmware"),
            "serial_number": device.get("serial_number"),
            "serial_port": device.get("last_port"),
            "first_seen": device.get("first_seen"),
            "last_seen": device.get("last_seen"),
        },
        "measurement": {
            "available": latest is not None,
            "completed_at": completed_at,
            "age_hours": age_hours,
            "fresh": age_hours is not None and age_hours <= 2.5,
            "hour_index": int(latest["hour_index"]) if latest else None,
            "raw_cph": int(latest["raw_cph"]) if latest else None,
            "bq_m3": current_bq,
            "pci_l": _pci(current_bq),
            # Always expose the currently configured factor as the active factor.
            # The factor stored with the latest historical measurement remains available
            # separately for traceability and reproducibility.
            "factor_bq_m3_per_cph": settings.factor_bq_m3_per_cph,
            "measurement_factor_bq_m3_per_cph": float(latest["factor"]) if latest else None,
            "source": latest.get("source") if latest else "spir_hourly_history",
            "status": _status(current_bq, settings),
            "location_id": latest.get("location_id") if latest else None,
            "location_name": latest.get("location_name") if latest else None,
            "session_id": latest.get("session_id") if latest else None,
            "session_title": latest.get("session_title") if latest else None,
        },
        "statistics": {},
        "protocol": protocol,
        "database": {
            "path": str(storage.path),
            "sample_count": storage.count(current_device_id),
            "total_sample_count": storage.count(),
            "size_bytes": data_summary.get("database_size_bytes", 0),
            "first_measurement": data_summary.get("first_measurement"),
            "last_measurement": data_summary.get("last_measurement"),
            "integrity": data_summary.get("integrity"),
            "schema_version": data_summary.get("schema_version"),
        },
        "catalog": {
            "locations": data_summary.get("locations", 0),
            "maps": data_summary.get("maps", 0),
            "sessions": data_summary.get("sessions", 0),
            "events": data_summary.get("events", 0),
            "reports": data_summary.get("reports", 0),
            "campaigns": data_summary.get("campaigns", 0),
            "devices": data_summary.get("devices", 0),
        },
        "settings": settings.public_dict(),
    }
    for period, values in stats.items():
        mean = values.get("mean_bq_m3")
        minimum = values.get("minimum_bq_m3")
        maximum = values.get("maximum_bq_m3")
        state["statistics"][period] = {
            **values,
            "mean_pci_l": _pci(float(mean)) if mean is not None else None,
            "minimum_pci_l": _pci(float(minimum)) if minimum is not None else None,
            "maximum_pci_l": _pci(float(maximum)) if maximum is not None else None,
            "status": _status(float(mean) if mean is not None else None, settings),
        }
    return state
