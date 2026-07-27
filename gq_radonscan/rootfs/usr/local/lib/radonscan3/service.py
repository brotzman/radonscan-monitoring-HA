from __future__ import annotations

import logging
import signal
import threading

from .config import Settings
from . import __version__
from .device import Collector
from .mqtt import MqttPublisher
from .gmcmap import GmcMapClient, GmcMapError
from .homeassistant import HomeAssistantClient, HomeAssistantError
from .state import build_state
from .polling import update_connection_runtime
from .storage import Storage
from .web import WebServer

LOGGER = logging.getLogger(__name__)


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if settings.diagnostic_logging:
        logging.getLogger("radonscan3").setLevel(logging.DEBUG)


def main() -> int:
    settings = Settings.load()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(settings)

    storage = Storage(settings.data_dir / "radonscan_v3.sqlite3")
    collector = Collector(settings)
    mqtt = MqttPublisher(settings, storage.set_runtime)
    web = WebServer(settings, storage)
    gmcmap = GmcMapClient(settings, storage)
    ha = HomeAssistantClient(settings.homeassistant_access_token)
    storage.record_factor_configuration(settings.factor_bq_m3_per_cph, source="app_configuration", note="Active conversion factor at service start")
    stop = threading.Event()

    def handle_signal(signum, frame) -> None:
        LOGGER.info("Stopping after signal %s", signum)
        stop.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    mqtt.start()
    web.start()
    LOGGER.info("Radon Monitoring %s web interface listening on port %s", __version__, settings.web_port)
    LOGGER.info("Read-only polling interval: %s seconds", settings.scan_interval)
    LOGGER.info(
        "Serial mode: %s%s",
        "fixed" if settings.serial_port and settings.serial_port.lower() not in {"auto", "automatic", "detect", "discovery"} else "automatic",
        f" ({settings.serial_port})" if settings.serial_port and settings.serial_port.lower() not in {"auto", "automatic", "detect", "discovery"} else "",
    )

    try:
        while not stop.is_set():
            result = collector.scan()
            if result.connected and result.snapshot is not None:
                storage.upsert_device(
                    device_id=result.device_id,
                    model=result.model or "GQ RadonScan",
                    firmware=result.firmware,
                    serial_number=result.serial_number,
                    port=result.port,
                    seen_at=result.detected_at,
                )
                skip_backfill_once = bool(storage.get_runtime("skip_history_backfill_once", False))
                imported = storage.import_snapshot(
                    device_id=result.device_id,
                    snapshot=result.snapshot,
                    detected_at=result.detected_at,
                    backfill=settings.backfill_history and not skip_backfill_once,
                )
                if skip_backfill_once:
                    storage.set_runtime("skip_history_backfill_once", False)
                update_connection_runtime(storage, result)
                protocol = result.snapshot.as_dict()
                protocol.update(
                    {
                        "status": "decoded",
                        "transport": "GETVER + SPIR",
                        "imported": imported,
                    }
                )
                storage.set_runtime("protocol", protocol)
                if imported.get("campaign_reset"):
                    LOGGER.warning("Device history reset detected; started a new measurement campaign")
                    if ha.available:
                        try:
                            ha.fire_event("radon_monitoring_campaign_started", {"device_id": result.device_id, "reason": "device_history_reset"})
                        except HomeAssistantError as exc:
                            LOGGER.debug("Could not emit Home Assistant event: %s", exc)
                LOGGER.info(
                    "RadonScan read: index=%s raw=%s bq_m3=%s imported=%s",
                    protocol.get("latest_hour_index"),
                    protocol.get("latest_raw_cph"),
                    protocol.get("latest_bq_m3"),
                    imported.get("inserted"),
                )
                if gmcmap.should_auto_upload():
                    try:
                        uploaded = gmcmap.upload_next(trigger="automatic")
                        LOGGER.info("GMCMap radon upload successful: %s pCi/L", uploaded.get("pci_l"))
                        if ha.available:
                            try:
                                ha.fire_event("radon_monitoring_worldmap_uploaded", uploaded)
                            except HomeAssistantError as exc:
                                LOGGER.debug("Could not emit Home Assistant event: %s", exc)
                    except GmcMapError as exc:
                        LOGGER.warning("GMCMap radon upload failed: %s", exc)
                        if ha.available:
                            try:
                                ha.fire_event("radon_monitoring_worldmap_failed", {"error": str(exc)})
                            except HomeAssistantError as event_exc:
                                LOGGER.debug("Could not emit Home Assistant event: %s", event_exc)
            else:
                update_connection_runtime(storage, result)
                if result.port:
                    LOGGER.warning(
                        "RadonScan not available on %s [%s]: %s",
                        result.port,
                        result.error_code or "read_error",
                        result.error,
                    )
                else:
                    LOGGER.warning(
                        "RadonScan not available [%s]: %s",
                        result.error_code or "not_detected",
                        result.error,
                    )

            storage.prune(settings.history_retention_days)
            mqtt.publish(build_state(storage, settings))
            stop.wait(settings.scan_interval if result.connected else min(30, settings.scan_interval))
    finally:
        web.stop()
        mqtt.stop()
    return 0
