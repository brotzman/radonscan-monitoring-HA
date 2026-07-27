import json
from types import SimpleNamespace

from radonscan3.mqtt import MqttPublisher


class FakeClient:
    def __init__(self):
        self.messages = []

    def publish(self, topic, payload=None, qos=0, retain=False):
        self.messages.append((topic, payload, qos, retain))
        return SimpleNamespace(rc=0)


def _publisher(preferred_unit="pCi/L"):
    settings = SimpleNamespace(
        mqtt_topic_prefix="gq_radonscan",
        discovery_prefix="homeassistant",
        language="de",
        device_name="GQ RadonScan",
        preferred_unit=preferred_unit,
    )
    publisher = MqttPublisher.__new__(MqttPublisher)
    publisher.settings = settings
    publisher.runtime_callback = lambda *args, **kwargs: None
    publisher.host = "core-mosquitto"
    publisher.port = 1883
    publisher.username = None
    publisher.password = None
    publisher.connected = None
    publisher._discovery_device_id = None
    publisher._last_state = {}
    publisher.client = FakeClient()
    return publisher


def _state():
    return {
        "device": {"device_id": "RS-123", "model": "GQ RadonScan", "firmware": "1.0"},
        "measurement": {"bq_m3": 92.4, "pci_l": 2.497, "raw_cph": 60, "hour_index": 10, "completed_at": "2026-07-27T08:00:00Z"},
        "statistics": {
            "24h": {"mean_bq_m3": 88.1, "mean_pci_l": 2.381},
            "7d": {"mean_bq_m3": 79.3, "mean_pci_l": 2.143},
            "30d": {"mean_bq_m3": 70.0, "mean_pci_l": 1.892},
        },
        "database": {"sample_count": 100},
        "connection": {"connected": True},
    }


def test_home_assistant_discovery_exposes_only_three_bq_entities():
    publisher = _publisher(preferred_unit="pCi/L")
    publisher._publish_discovery(_state())

    configs = {}
    deletions = set()
    for topic, payload, qos, retain in publisher.client.messages:
        assert retain is True
        assert qos == 1
        if payload == "":
            deletions.add(topic)
        else:
            configs[topic] = json.loads(payload)

    expected_topics = {
        "homeassistant/sensor/gq_radonscan/radon_hourly/config",
        "homeassistant/sensor/gq_radonscan/average_24h/config",
        "homeassistant/sensor/gq_radonscan/average_7d/config",
    }
    assert set(configs) == expected_topics

    for payload in configs.values():
        assert payload["unit_of_measurement"] == "Bq/m³"
        assert payload["state_class"] == "measurement"
        # Keep discovery compatible with Home Assistant releases that predate
        # the dedicated radon device class and stricter origin validation.
        assert "device_class" not in payload
        assert "origin" not in payload
        assert payload["device"]["sw_version"]
        assert "serial_number" not in payload["device"]
        assert "json_attributes_topic" not in payload
        assert "pci_l" not in payload["value_template"]

    assert "measurement.bq_m3" in configs["homeassistant/sensor/gq_radonscan/radon_hourly/config"]["value_template"]
    assert "mean_bq_m3" in configs["homeassistant/sensor/gq_radonscan/average_24h/config"]["value_template"]
    assert "mean_bq_m3" in configs["homeassistant/sensor/gq_radonscan/average_7d/config"]["value_template"]

    expected_deletions = {
        "homeassistant/sensor/rs_123/average_30d/config",
        "homeassistant/sensor/rs_123/hour_index/config",
        "homeassistant/sensor/rs_123/raw_cph/config",
        "homeassistant/sensor/rs_123/last_update/config",
        "homeassistant/sensor/rs_123/sample_count/config",
        "homeassistant/binary_sensor/rs_123/connected/config",
    }
    assert expected_deletions <= deletions
    assert "homeassistant/sensor/rs_123/radon_hourly/config" in deletions
    assert "homeassistant/sensor/rs_123/average_24h/config" in deletions
    assert "homeassistant/sensor/rs_123/average_7d/config" in deletions


def test_discovery_is_published_without_a_connected_or_known_device():
    publisher = _publisher()
    publisher._publish_discovery({})
    configs = {
        topic: json.loads(payload)
        for topic, payload, qos, retain in publisher.client.messages
        if payload not in (None, "")
    }
    assert set(configs) == {
        "homeassistant/sensor/gq_radonscan/radon_hourly/config",
        "homeassistant/sensor/gq_radonscan/average_24h/config",
        "homeassistant/sensor/gq_radonscan/average_7d/config",
    }
    for payload in configs.values():
        assert payload["device"]["identifiers"] == ["radon_monitoring_gq_radonscan"]
        assert payload["device"]["name"] == "GQ RadonScan"
        assert "value_json.device.device_id" not in payload["value_template"]
