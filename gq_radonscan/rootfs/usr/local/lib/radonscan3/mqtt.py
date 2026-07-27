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
        self._last_state: dict[str, Any] = {}
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
            self.client.will_set(self.availability_topic, "offline", qos=1, retain=True)

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
            # Force discovery and legacy cleanup to be replayed after every MQTT
            # reconnect. This is important after Home Assistant or Mosquitto was
            # restarted while the app process stayed alive.
            self._discovery_device_id = None
            client.publish(self.availability_topic, "online", qos=1, retain=True)
            # Publish the three Home Assistant entities immediately. Discovery
            # must not depend on a currently connected RadonScan or on an
            # already imported measurement.
            self._publish_discovery(self._last_state)
            self._runtime(True)
            LOGGER.info("Connected to MQTT broker %s:%s", self.host, self.port)
        else:
            self._runtime(False, str(reason_code))

    def _on_disconnect(self, client, userdata, *args) -> None:
        self.connected.clear()
        self._discovery_device_id = None
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
            self.client.publish(self.availability_topic, "offline", qos=1, retain=True)
            self.client.disconnect()
        except Exception:
            pass
        finally:
            self.client.loop_stop()

    @property
    def discovery_node_id(self) -> str:
        """Stable MQTT discovery node for the single RadonScan device.

        Discovery used to follow the runtime device id. That made the entity
        disappear or move between device cards when the serial device was
        unavailable during startup. A fixed node keeps the same three entities
        present independently of connection state and measurement history.
        """
        return "gq_radonscan"

    def _legacy_discovery_node_ids(self, state: dict[str, Any]) -> tuple[str, ...]:
        """Return node identifiers used by current and historical releases."""
        device = state.get("device") or {}
        candidates = {
            str(device.get("device_id") or ""),
            str(device.get("serial_number") or ""),
            str(self.settings.device_name or ""),
            "radonscan",
            "gq_radonscan",
            "gq_radonscan_v4",
        }
        return tuple(sorted({slug(value) for value in candidates if value.strip()}))

    def _purge_legacy_discovery(self, state: dict[str, Any]) -> None:
        if self.client is None:
            return
        obsolete_sensor_ids = (
            "average_30d",
            "hour_index",
            "raw_cph",
            "last_update",
            "sample_count",
            "stored_hours",
        )
        current_sensor_ids = ("radon_hourly", "average_24h", "average_7d")
        stable_node = self.discovery_node_id
        for node_id in self._legacy_discovery_node_ids(state):
            for object_id in obsolete_sensor_ids:
                self.client.publish(
                    f"{self.settings.discovery_prefix}/sensor/{node_id}/{object_id}/config",
                    "",
                    qos=1,
                    retain=True,
                )
                self.client.publish(
                    f"{self.settings.discovery_prefix}/sensor/{node_id}_{object_id}/config",
                    "",
                    qos=1,
                    retain=True,
                )
            # Remove the three desired sensors only from historical dynamic
            # node ids. They are republished below on the stable node.
            if node_id != stable_node:
                for object_id in current_sensor_ids:
                    self.client.publish(
                        f"{self.settings.discovery_prefix}/sensor/{node_id}/{object_id}/config",
                        "",
                        qos=1,
                        retain=True,
                    )
                    self.client.publish(
                        f"{self.settings.discovery_prefix}/sensor/{node_id}_{object_id}/config",
                        "",
                        qos=1,
                        retain=True,
                    )
            self.client.publish(
                f"{self.settings.discovery_prefix}/binary_sensor/{node_id}/connected/config",
                "",
                qos=1,
                retain=True,
            )
            self.client.publish(
                f"{self.settings.discovery_prefix}/binary_sensor/{node_id}_connected/config",
                "",
                qos=1,
                retain=True,
            )

    def _publish_discovery(self, state: dict[str, Any] | None = None) -> None:
        if self.client is None:
            return
        state = state or {}
        device_state = state.get("device") or {}
        device_id = self.discovery_node_id
        if self._discovery_device_id == device_id:
            return
        t = load(resolve(self.settings.language))
        device = {
            "identifiers": ["radon_monitoring_gq_radonscan"],
            "name": self.settings.device_name,
            "manufacturer": "GQ Electronics",
            "model": device_state.get("model") or "RadonScan",
            "sw_version": __version__,
        }
        base = {
            "state_topic": self.state_topic,
            "availability_topic": self.availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": {k: v for k, v in device.items() if v},
        }

        # Home Assistant intentionally exposes only the three user-facing radon
        # entities requested for dashboards and history. Discovery and value
        # extraction are independent of the temporary serial connection state.
        unit = "Bq/m³"
        precision = 1
        sensors = {
            "radon_hourly": {
                "name": t["hourly_value"],
                "value_template": "{{ value_json.measurement.bq_m3 }}",
                "unit_of_measurement": unit,
                "state_class": "measurement",
                "icon": "mdi:radioactive",
                "suggested_display_precision": precision,
            },
            "average_24h": {
                "name": t["average_24h"],
                "value_template": "{{ value_json.statistics['24h']['mean_bq_m3'] }}",
                "unit_of_measurement": unit,
                "state_class": "measurement",
                "icon": "mdi:clock-outline",
                "suggested_display_precision": precision,
            },
            "average_7d": {
                "name": t["average_7d"],
                "value_template": "{{ value_json.statistics['7d']['mean_bq_m3'] }}",
                "unit_of_measurement": unit,
                "state_class": "measurement",
                "icon": "mdi:calendar-week",
                "suggested_display_precision": precision,
            },
        }

        self._purge_legacy_discovery(state)
        for object_id, extra in sensors.items():
            payload = {
                **base,
                **extra,
                "unique_id": f"radon_monitoring_{device_id}_{object_id}",
            }
            topic = f"{self.settings.discovery_prefix}/sensor/{device_id}/{object_id}/config"
            result = self.client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=True)
            if getattr(result, "rc", 0) != 0:
                LOGGER.warning("MQTT discovery publish failed for %s: rc=%s", topic, getattr(result, "rc", None))

        self._discovery_device_id = device_id

    def publish(self, state: dict[str, Any]) -> None:
        self._last_state = state
        if self.client is None or not self.connected.is_set():
            return
        self._publish_discovery(state)
        result = self.client.publish(self.state_topic, json.dumps(state, ensure_ascii=False, default=str), qos=1, retain=True)
        if getattr(result, "rc", 0) != 0:
            LOGGER.warning("MQTT state publish failed: rc=%s", getattr(result, "rc", None))
