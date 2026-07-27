from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path

LOGGER = logging.getLogger(__name__)
SUPPORTED_LANGUAGES = ("auto", "de", "en", "es", "fr", "hr", "it", "nl", "pl")
SUPPORTED_UNITS = ("Bq/m3", "pCi/L")
SUPPORTED_LOCATION_DISPLAY_MODES = ("full", "reduced", "hidden")
DEFAULT_SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"


def _as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    web_port: int
    device_name: str
    scan_interval: int
    preferred_unit: str
    language: str
    warning_threshold_bq_m3: float
    danger_threshold_bq_m3: float
    factor_bq_m3_per_cph: float
    backfill_history: bool
    history_retention_days: int
    serial_port: str
    serial_timeout_seconds: float
    mqtt_topic_prefix: str
    discovery_prefix: str
    data_management_enabled: bool
    diagnostic_logging: bool
    log_level: str
    minimum_data_coverage_percent: float
    report_author: str
    report_organisation: str
    report_disclaimer: str
    gmcmap_enabled: bool
    gmcmap_auto_upload: bool
    gmcmap_account_id: str
    gmcmap_device_id: str
    gmcmap_upload_interval_minutes: int
    gmcmap_max_age_hours: int
    gmcmap_retry_limit: int
    analysis_timezone: str
    location_display_mode: str
    homeassistant_access_token: str

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Settings":
        config_path = Path(path or os.environ.get("CONFIG_PATH", "/data/options.json"))
        raw: dict[str, object] = {}
        if config_path.is_file():
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            LOGGER.warning("Options file %s does not exist; using defaults", config_path)

        language = str(raw.get("language", "auto"))
        if language not in SUPPORTED_LANGUAGES:
            language = "auto"
        unit = str(raw.get("preferred_unit", "Bq/m3"))
        if unit not in SUPPORTED_UNITS:
            unit = "Bq/m3"

        warning = float(raw.get("warning_threshold_bq_m3", 100.0))
        danger = float(raw.get("danger_threshold_bq_m3", 300.0))
        if danger < warning:
            warning, danger = danger, warning

        factor = float(raw.get("factor_bq_m3_per_cph", 1.530))
        if not 0.001 <= factor <= 1000:
            raise ValueError("factor_bq_m3_per_cph must be between 0.001 and 1000")

        scan_interval = int(raw.get("scan_interval", 300))
        if not 30 <= scan_interval <= 3600:
            raise ValueError("scan_interval must be between 30 and 3600 seconds")

        minimum_coverage = float(raw.get("minimum_data_coverage_percent", 95.0))
        minimum_coverage = max(50.0, min(100.0, minimum_coverage))
        location_display_mode = str(raw.get("location_display_mode", "full")).strip().lower()
        if location_display_mode not in SUPPORTED_LOCATION_DISPLAY_MODES:
            location_display_mode = "full"

        serial_port = str(raw.get("serial_port", DEFAULT_SERIAL_PORT)).strip()
        # Existing Home Assistant installations may retain an empty option value
        # during an upgrade. Migrate that empty value to the known stable by-id
        # path. An explicit "auto" choice remains automatic and is never overridden.
        if not serial_port:
            serial_port = DEFAULT_SERIAL_PORT

        return cls(
            data_dir=Path(os.environ.get("DATA_DIR", "/data")),
            web_port=int(os.environ.get("WEB_PORT", "8099")),
            device_name=str(raw.get("device_name", "GQ RadonScan")).strip() or "GQ RadonScan",
            scan_interval=scan_interval,
            preferred_unit=unit,
            language=language,
            warning_threshold_bq_m3=max(0.0, warning),
            danger_threshold_bq_m3=max(0.0, danger),
            factor_bq_m3_per_cph=factor,
            backfill_history=_as_bool(raw.get("backfill_history"), True),
            history_retention_days=max(30, min(3650, int(raw.get("history_retention_days", 1095)))),
            serial_port=serial_port,
            serial_timeout_seconds=max(0.5, min(15.0, float(raw.get("serial_timeout_seconds", 3.0)))),
            mqtt_topic_prefix=str(raw.get("mqtt_topic_prefix", "gq_radonscan")).strip(" /") or "gq_radonscan",
            discovery_prefix=str(raw.get("discovery_prefix", "homeassistant")).strip(" /") or "homeassistant",
            data_management_enabled=_as_bool(raw.get("data_management_enabled"), True),
            diagnostic_logging=_as_bool(raw.get("diagnostic_logging"), False),
            log_level=str(raw.get("log_level", "info")).upper(),
            minimum_data_coverage_percent=minimum_coverage,
            report_author=str(raw.get("report_author", "")).strip(),
            report_organisation=str(raw.get("report_organisation", "")).strip(),
            report_disclaimer=str(raw.get("report_disclaimer", "")).strip(),
            gmcmap_enabled=_as_bool(raw.get("gmcmap_enabled"), False),
            gmcmap_auto_upload=_as_bool(raw.get("gmcmap_auto_upload"), False),
            gmcmap_account_id=str(raw.get("gmcmap_account_id", "")).strip(),
            gmcmap_device_id=str(raw.get("gmcmap_device_id", "")).strip(),
            gmcmap_upload_interval_minutes=max(5, min(1440, int(raw.get("gmcmap_upload_interval_minutes", 60)))),
            gmcmap_max_age_hours=max(1, min(8760, int(raw.get("gmcmap_max_age_hours", 72)))),
            gmcmap_retry_limit=max(1, min(20, int(raw.get("gmcmap_retry_limit", 8)))),
            analysis_timezone=str(raw.get("analysis_timezone", "auto")).strip() or "auto",
            location_display_mode=location_display_mode,
            homeassistant_access_token=str(raw.get("homeassistant_access_token", "")).strip(),
        )

    def public_dict(self) -> dict[str, object]:
        return {
            "device_name": self.device_name,
            "scan_interval": self.scan_interval,
            "preferred_unit": self.preferred_unit,
            "language": self.language,
            "warning_threshold_bq_m3": self.warning_threshold_bq_m3,
            "danger_threshold_bq_m3": self.danger_threshold_bq_m3,
            "factor_bq_m3_per_cph": self.factor_bq_m3_per_cph,
            "backfill_history": self.backfill_history,
            "history_retention_days": self.history_retention_days,
            "serial_port": self.serial_port or "auto",
            "serial_timeout_seconds": self.serial_timeout_seconds,
            "mqtt_topic_prefix": self.mqtt_topic_prefix,
            "data_management_enabled": self.data_management_enabled,
            "diagnostic_logging": self.diagnostic_logging,
            "minimum_data_coverage_percent": self.minimum_data_coverage_percent,
            "report_author": self.report_author,
            "report_organisation": self.report_organisation,
            "gmcmap_enabled": self.gmcmap_enabled,
            "gmcmap_auto_upload": self.gmcmap_auto_upload,
            "gmcmap_configured": bool(self.gmcmap_account_id and self.gmcmap_device_id),
            "gmcmap_account_id_masked": (self.gmcmap_account_id[:2] + "••••" + self.gmcmap_account_id[-2:]) if len(self.gmcmap_account_id) > 4 else "",
            "gmcmap_device_id_masked": (self.gmcmap_device_id[:2] + "••••" + self.gmcmap_device_id[-2:]) if len(self.gmcmap_device_id) > 4 else "",
            "gmcmap_upload_interval_minutes": self.gmcmap_upload_interval_minutes,
            "gmcmap_max_age_hours": self.gmcmap_max_age_hours,
            "gmcmap_retry_limit": self.gmcmap_retry_limit,
            "analysis_timezone": self.analysis_timezone,
            "location_display_mode": self.location_display_mode,
            "homeassistant_access_token_configured": bool(self.homeassistant_access_token),
        }
