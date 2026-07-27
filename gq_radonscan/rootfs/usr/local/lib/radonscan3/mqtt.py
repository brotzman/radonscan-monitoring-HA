from __future__ import annotations

import json
import logging
import os
import re
import threading
from typing import Any

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None

from . import __version__
from .config import Settings
from .i18n import load, resolve

LOGGER = logging.getLogger(__name__)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "gq_radonscan"


class MqttPublisher:
    def __init__(self, settings: Settings, runtime_callback) -> None:
        self.settings = settings
        self.runtime_callback = runtime_callback
        self.host = os.environ.get("MQTT_HOST", "core-mosquitto")
        self.port = int(os.environ.get("MQTT_PORT", "1883"))
        self.username = os.environ.get("MQTT_USERNAME")
        self.password = os.environ.get("MQTT_PASSWORD")
        self.connected = threading.Event()
        self._discovery_device_id: str | None = None
        self.client = None
        if mqtt is not None:
            try:
                api = mqtt.CallbackAPIVersion.VERSION2  # type: ignore[attr-defined]
                self.client = mqtt.Client(api, client_id="gq_radonscan_v4")
            except (AttributeError, TypeError):
                self.client = mqtt.Client(client_id="gq_radonscan_v4")
            if self.username:
                self.client.username_pw_set(self.username, self.password)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.will_set(self.availability_topic, "offline", retain=True)

    @property
    def state_topic(self) -> str:
        return f"{self.settings.mqtt_topic_prefix}/state"

    @property
    def availability_topic(self) -> str:
        return f"{self.settings.mqtt_topic_prefix}/availability"

    def _runtime(self, connected: bool, error: str | None = None) -> None:
        self.runtime_callback(
            "mqtt",
            {
                "connected": connected,
                "host": self.host,
                "port": self.port,
                "error": error,
            },
        )

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        success = reason_code == 0 or str(reason_code).lower() == "success"
        if success:
            self.connected.set()
            client.publish(self.availability_topic, "online", retain=True)
            self._runtime(True)
            LOGGER.info("Connected to MQTT broker %s:%s", self.host, self.port)
        else:
            self._runtime(False, str(reason_code))

    def _on_disconnect(self, client, userdata, *args) -> None:
        self.connected.clear()
        self._runtime(False, "disconnected")

    def start(self) -> None:
        if self.client is None:
            self._runtime(False, "paho-mqtt unavailable")
            return
        try:
            self.client.connect_async(self.host, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as exc:
            LOGGER.warning("MQTT start failed: %s", exc)
            self._runtime(False, str(exc))

    def stop(self) -> None:
        if self.client is None:
            return
        try:
            self.client.publish(self.availability_topic, "offline", retain=True)
            self.client.disconnect()
        except Exception:
            pass
        finally:
            self.client.loop_stop()

    def _publish_discovery(self, state: dict[str, Any]) -> None:
        if self.client is None:
            return
        device_id = slug(str(state.get("device", {}).get("device_id") or "radonscan"))
        if self._discovery_device_id == device_id:
            return
        t = load(resolve(self.settings.language))
        device = {
            "identifiers": [f"gq_radonscan_{device_id}"],
            "name": self.settings.device_name,
            "manufacturer": "GQ Electronics",
            "model": state.get("device", {}).get("model") or "RadonScan",
            "sw_version": state.get("device", {}).get("firmware"),
        }
        base = {
            "state_topic": self.state_topic,
            "availability_topic": self.availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": {k: v for k, v in device.items() if v},
            "origin": {"name": "Radon Monitoring", "sw": __version__},
        }

        expected_device = json.dumps(str(state.get("device", {}).get("device_id") or ""))

        def guarded(expression: str, fallback: str = "{{ none }}") -> str:
            return (
                "{% if value_json.device.device_id == " + expected_device + " %}"
                + expression
                + "{% else %}" + fallback + "{% endif %}"
            )

        # Home Assistant intentionally exposes only the three user-facing radon
        # entities requested for dashboards and history.  These entities always
        # use Bq/m³, independently of the display unit selected inside the app.
        unit = "Bq/m³"
        precision = 1
        sensors = {
            "radon_hourly": {
                "name": t["hourly_value"],
                "value_template": guarded("{{ value_json.measurement.bq_m3 }}"),
                "unit_of_measurement": unit,
                "device_class": "radon",
                "state_class": "measurement",
                "icon": "mdi:radioactive",
                "suggested_display_precision": precision,
            },
            "average_24h": {
                "name": t["average_24h"],
                "value_template": guarded("{{ value_json.statistics['24h']['mean_bq_m3'] }}"),
                "unit_of_measurement": unit,
                "device_class": "radon",
                "state_class": "measurement",
                "icon": "mdi:clock-outline",
                "suggested_display_precision": precision,
            },
            "average_7d": {
                "name": t["average_7d"],
                "value_template": guarded("{{ value_json.statistics['7d']['mean_bq_m3'] }}"),
                "unit_of_measurement": unit,
                "device_class": "radon",
                "state_class": "measurement",
                "icon": "mdi:calendar-week",
                "suggested_display_precision": precision,
            },
        }

        # Delete retained MQTT discovery configurations from older releases so
        # Home Assistant removes the obsolete entities automatically after the
        # first successful MQTT connection following an upgrade.
        obsolete_sensor_ids = (
            "average_30d",
            "hour_index",
            "raw_cph",
            "last_update",
            "sample_count",
        )
        for object_id in obsolete_sensor_ids:
            topic = f"{self.settings.discovery_prefix}/sensor/{device_id}/{object_id}/config"
            self.client.publish(topic, "", retain=True)
        self.client.publish(
            f"{self.settings.discovery_prefix}/binary_sensor/{device_id}/connected/config",
            "",
            retain=True,
        )
        for object_id, extra in sensors.items():
            payload = {
                **base,
                **extra,
                "unique_id": f"gq_radonscan_{device_id}_{object_id}",
            }
            topic = f"{self.settings.discovery_prefix}/sensor/{device_id}/{object_id}/config"
            self.client.publish(topic, json.dumps(payload, ensure_ascii=False), retain=True)

        self._discovery_device_id = device_id

    def publish(self, state: dict[str, Any]) -> None:
        if self.client is None or not self.connected.is_set():
            return
        self._publish_discovery(state)
        self.client.publish(self.state_topic, json.dumps(state, ensure_ascii=False, default=str), retain=True)
