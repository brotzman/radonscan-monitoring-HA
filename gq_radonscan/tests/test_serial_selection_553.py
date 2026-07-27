from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from radonscan3.device import Collector, ScanResult
from radonscan3.polling import update_connection_runtime


class RuntimeStorage:
    def __init__(self):
        self.payload = None

    def set_runtime(self, key, payload):
        assert key == "connection"
        self.payload = payload


def settings(serial_port):
    return SimpleNamespace(
        serial_port=serial_port,
        serial_timeout_seconds=3.0,
        factor_bq_m3_per_cph=1.53,
        diagnostic_logging=False,
    )


def test_fixed_port_is_used_exclusively():
    fixed = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
    collector = Collector(settings(fixed))
    with patch("radonscan3.device.glob.glob", return_value=["/dev/ttyUSB9"]):
        assert collector._ports() == (fixed,)


def test_auto_mode_skips_zigbee_and_ttyama_and_deduplicates_aliases():
    collector = Collector(settings("auto"))
    by_id = [
        "/dev/serial/by-id/usb-Itead_Sonoff_Zigbee_3.0_USB_Dongle-if00-port0",
        "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
    ]

    def fake_glob(pattern):
        if pattern == "/dev/serial/by-id/*":
            return by_id
        if pattern == "/dev/ttyUSB*":
            return ["/dev/ttyUSB0", "/dev/ttyUSB1"]
        if pattern == "/dev/ttyACM*":
            return []
        return []

    def fake_realpath(port):
        if port.endswith("usb-1a86_USB_Serial-if00-port0") or port == "/dev/ttyUSB0":
            return "/dev/ttyUSB0"
        if "Sonoff_Zigbee" in port or port == "/dev/ttyUSB1":
            return "/dev/ttyUSB1"
        return port

    fake_list_ports = SimpleNamespace(comports=lambda: [SimpleNamespace(device="/dev/ttyAMA10")])
    with patch("radonscan3.device.glob.glob", side_effect=fake_glob), \
         patch("radonscan3.device.os.path.realpath", side_effect=fake_realpath), \
         patch("radonscan3.device.list_ports", fake_list_ports):
        assert collector._ports() == (
            "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
        )


def test_connection_error_classification_is_actionable():
    collector = Collector(settings("auto"))
    busy = OSError(16, "Device or resource busy")
    missing = OSError(2, "No such file or directory")
    denied = PermissionError(13, "Permission denied")
    assert collector._classify_error(busy) == "port_busy"
    assert collector._classify_error(missing) == "port_not_found"
    assert collector._classify_error(denied) == "permission_denied"
    assert collector._classify_error(TimeoutError("no response to GETVER")) == "no_response"
    assert collector._classify_error(ValueError("GETVER did not identify RadonScan: deadbeef")) == "wrong_device"


def test_runtime_contains_error_code_and_checked_port():
    result = ScanResult(
        False,
        datetime.now(timezone.utc),
        "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
        None,
        None,
        None,
        None,
        "Device or resource busy",
        ("/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",),
        "port_busy",
    )
    storage = RuntimeStorage()
    payload = update_connection_runtime(storage, result)
    assert payload["port"].endswith("usb-1a86_USB_Serial-if00-port0")
    assert payload["error_code"] == "port_busy"
    assert storage.payload == payload


def test_empty_option_migrates_to_fixed_port_but_explicit_auto_is_preserved(tmp_path):
    import json
    from radonscan3.config import DEFAULT_SERIAL_PORT, Settings

    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"serial_port": ""}), encoding="utf-8")
    assert Settings.load(empty).serial_port == DEFAULT_SERIAL_PORT

    automatic = tmp_path / "auto.json"
    automatic.write_text(json.dumps({"serial_port": "auto"}), encoding="utf-8")
    assert Settings.load(automatic).serial_port == "auto"
