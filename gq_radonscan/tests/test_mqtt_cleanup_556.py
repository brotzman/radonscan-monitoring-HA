from types import SimpleNamespace

from radonscan3.mqtt import MqttPublisher


class FakeClient:
    def __init__(self):
        self.messages = []

    def publish(self, topic, payload=None, retain=False):
        self.messages.append((topic, payload, retain))
        return SimpleNamespace(rc=0)


def publisher():
    item = MqttPublisher.__new__(MqttPublisher)
    item.settings = SimpleNamespace(
        mqtt_topic_prefix="gq_radonscan",
        discovery_prefix="homeassistant",
        language="de",
        device_name="GQ RadonScan",
        preferred_unit="Bq/m³",
    )
    item.runtime_callback = lambda *args, **kwargs: None
    item.host = "core-mosquitto"
    item.port = 1883
    item.username = None
    item.password = None
    item._discovery_device_id = "old_device"
    item.client = FakeClient()
    return item


def state():
    return {
        "device": {
            "device_id": "RS-123",
            "serial_number": "Serial 456",
            "model": "GQ RadonScan",
            "firmware": "1.0",
        },
        "measurement": {"bq_m3": 92.4},
        "statistics": {
            "24h": {"mean_bq_m3": 88.1},
            "7d": {"mean_bq_m3": 79.3},
        },
    }


def test_cleanup_covers_device_serial_and_generic_aliases():
    item = publisher()
    item._purge_legacy_discovery(state())
    deleted = {topic for topic, payload, retain in item.client.messages if payload == "" and retain}

    for node in ("rs_123", "serial_456", "radonscan", "gq_radonscan", "gq_radonscan_v4"):
        assert f"homeassistant/sensor/{node}/hour_index/config" in deleted
        assert f"homeassistant/sensor/{node}/raw_cph/config" in deleted
        assert f"homeassistant/sensor/{node}/last_update/config" in deleted
        assert f"homeassistant/sensor/{node}/sample_count/config" in deleted
        assert f"homeassistant/binary_sensor/{node}/connected/config" in deleted


def test_mqtt_reconnect_forces_discovery_republish():
    item = publisher()
    item.connected = SimpleNamespace(set=lambda: None, clear=lambda: None)
    item._runtime = lambda *args, **kwargs: None
    item._on_connect(item.client, None, None, 0)
    assert item._discovery_device_id is None

    item._discovery_device_id = "rs_123"
    item._on_disconnect(item.client, None)
    assert item._discovery_device_id is None
