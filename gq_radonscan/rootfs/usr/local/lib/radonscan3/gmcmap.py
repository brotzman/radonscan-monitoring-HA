from __future__ import annotations

from datetime import datetime, timezone
import logging
import urllib.error
import urllib.parse
import urllib.request

from .config import Settings
from .storage import Storage

LOGGER = logging.getLogger(__name__)
DEFAULT_ENDPOINT = "https://www.gmcmap.com/log2.asp"


class GmcMapError(RuntimeError):
    pass


class GmcMapClient:
    """Reliable queue-based upload to the GQ Radiation World Map."""

    def __init__(self, settings: Settings, storage: Storage) -> None:
        self.settings = settings
        self.storage = storage

    def configured(self) -> bool:
        return bool(self.settings.gmcmap_account_id and self.settings.gmcmap_device_id)

    @staticmethod
    def _mask(value: str) -> str:
        value = str(value or "")
        if len(value) <= 4:
            return "•" * len(value)
        return f"{value[:2]}{'•' * (len(value)-4)}{value[-2:]}"

    def status(self) -> dict[str, object]:
        latest = self.storage.latest()
        runtime = self.storage.get_runtime("gmcmap", {})
        return {
            "enabled": self.settings.gmcmap_enabled,
            "auto_upload": self.settings.gmcmap_auto_upload,
            "configured": self.configured(),
            "account_id_masked": self._mask(self.settings.gmcmap_account_id),
            "device_id_masked": self._mask(self.settings.gmcmap_device_id),
            "interval_minutes": self.settings.gmcmap_upload_interval_minutes,
            "max_age_hours": self.settings.gmcmap_max_age_hours,
            "retry_limit": self.settings.gmcmap_retry_limit,
            "endpoint": DEFAULT_ENDPOINT,
            "latest_available": latest is not None,
            "latest_measurement_at": latest.get("completed_at") if latest else None,
            "last_upload": runtime if isinstance(runtime, dict) else {},
            "queue": self.storage.worldmap_queue_summary(),
        }

    def refresh_queue(self) -> int:
        if not self.settings.gmcmap_enabled:
            return 0
        return self.storage.queue_worldmap_measurements(max_age_hours=self.settings.gmcmap_max_age_hours)

    def should_auto_upload(self) -> bool:
        if not (self.settings.gmcmap_enabled and self.settings.gmcmap_auto_upload and self.configured()):
            return False
        self.refresh_queue()
        if self.storage.next_worldmap_item() is None:
            return False
        runtime = self.storage.get_runtime("gmcmap", {})
        attempted = runtime.get("attempted_at") if isinstance(runtime, dict) else None
        if not attempted:
            return True
        try:
            previous = datetime.fromisoformat(str(attempted).replace("Z", "+00:00")).astimezone(timezone.utc)
            return (datetime.now(timezone.utc) - previous).total_seconds() >= self.settings.gmcmap_upload_interval_minutes * 60
        except (ValueError, TypeError):
            return True

    def upload_latest(self, *, trigger: str = "manual", user_name: str | None = None) -> dict[str, object]:
        self._validate()
        self.refresh_queue()
        latest = self.storage.latest()
        if not latest:
            raise GmcMapError("No completed local radon measurement is available")
        # Manual upload prioritises the latest reading and remains duplicate-safe.
        item = {
            "id": None,
            "measurement_at": latest.get("completed_at"),
            "bq_m3": latest.get("bq_m3"),
            "pci_l": float(latest.get("bq_m3")) / 37.0,
        }
        return self._upload_item(item, trigger=trigger, user_name=user_name)

    def upload_next(self, *, trigger: str = "automatic", user_name: str | None = None) -> dict[str, object]:
        self._validate()
        self.refresh_queue()
        item = self.storage.next_worldmap_item()
        if not item:
            raise GmcMapError("No pending World Map measurement is available")
        return self._upload_item(item, trigger=trigger, user_name=user_name)

    def _validate(self) -> None:
        if not self.settings.gmcmap_enabled:
            raise GmcMapError("GQ Radiation World Map upload is disabled in the app configuration")
        if not self.configured():
            raise GmcMapError("GMCMap Account ID and Device ID must be configured")

    def _upload_item(self, item: dict[str, object], *, trigger: str, user_name: str | None) -> dict[str, object]:
        bq_m3 = float(item["bq_m3"])
        pci_l = float(item.get("pci_l") or bq_m3 / 37.0)
        params = {
            "AID": self.settings.gmcmap_account_id,
            "GID": self.settings.gmcmap_device_id,
            "CPM": "0",
            "pCi": f"{pci_l:.4f}",
        }
        url = f"{DEFAULT_ENDPOINT}?{urllib.parse.urlencode(params)}"
        attempted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        result: dict[str, object] = {
            "ok": False,
            "trigger": trigger,
            "attempted_at": attempted_at,
            "measurement_at": item.get("measurement_at"),
            "bq_m3": round(bq_m3, 3),
            "pci_l": round(pci_l, 4),
            "response": "",
            "queue_id": item.get("id"),
        }
        error: str | None = None
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Radon-Monitoring/4.3.9", "Accept": "text/plain,text/html;q=0.9,*/*;q=0.8"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read(4096).decode("utf-8", errors="replace").strip()
                result["http_status"] = int(response.status)
                result["response"] = body
                lowered = body.lower()
                result["ok"] = 200 <= response.status < 300 and ("ok" in lowered or "success" in lowered)
                if not result["ok"]:
                    error = body or f"GMCMap returned HTTP {response.status}"
                    raise GmcMapError(error)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            error = str(exc)
            result["response"] = error
            self._record(result, user_name, error)
            raise GmcMapError(f"GMCMap upload failed: {exc}") from exc
        except GmcMapError:
            self._record(result, user_name, error or str(result.get("response") or "upload failed"))
            raise

        self._record(result, user_name, None)
        return result

    def _record(self, result: dict[str, object], user_name: str | None, error: str | None) -> None:
        queue_id = result.get("queue_id")
        if queue_id is not None:
            self.storage.update_worldmap_item(
                int(queue_id),
                ok=bool(result.get("ok")),
                error=error,
                retry_limit=self.settings.gmcmap_retry_limit,
            )
        self.storage.set_runtime("gmcmap", result)
        self.storage.record_worldmap_upload(result, user_name=user_name)
        self.storage.audit("gmcmap_upload", "gmcmap", result, user_name)
