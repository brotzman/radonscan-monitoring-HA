from __future__ import annotations

from .device import ScanResult
from .storage import Storage


def update_connection_runtime(storage: Storage, result: ScanResult) -> dict[str, object]:
    """Persist a consistent connection snapshot for connected and disconnected scans."""
    payload: dict[str, object] = {
        "connected": bool(result.connected),
        "status": "connected" if result.connected else "disconnected",
        "last_scan": result.detected_at.isoformat(timespec="seconds"),
        "port": result.port,
        "error": None if result.connected else result.error,
        "error_code": None if result.connected else result.error_code,
        "attempts": list(result.attempts),
    }
    storage.set_runtime("connection", payload)
    return payload
