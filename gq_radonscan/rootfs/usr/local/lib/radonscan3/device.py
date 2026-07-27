from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import glob
import hashlib
import logging
import os
import re
import time
from typing import Iterable

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - development host without pyserial
    serial = None
    list_ports = None

from .config import Settings
from .decoder import Snapshot, decode
from .protocol import (
    BLOCK_SIZE,
    GETSERIAL,
    GETVER,
    TARGET_ADDRESSES,
    build_spir_command,
    serial_number_text,
)

LOGGER = logging.getLogger(__name__)
AUTO_SERIAL_VALUES = {"", "auto", "automatic", "detect", "discovery"}
AUTO_SKIP_TOKENS = (
    "sonoff",
    "itead",
    "zigbee",
    "z-wave",
    "zwave",
    "conbee",
    "skyconnect",
    "ember",
)


@dataclass(frozen=True, slots=True)
class ScanResult:
    connected: bool
    detected_at: datetime
    port: str | None
    model: str | None
    firmware: str | None
    serial_number: str | None
    snapshot: Snapshot | None
    error: str | None
    attempts: tuple[str, ...]
    error_code: str | None = None

    @property
    def device_id(self) -> str:
        if self.serial_number:
            return re.sub(r"[^a-zA-Z0-9]+", "", self.serial_number).lower() or "radonscan"
        if self.firmware:
            return re.sub(r"[^a-zA-Z0-9]+", "", self.firmware).lower() or "radonscan"
        return "radonscan"


class Collector:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _configured_port(self) -> str | None:
        value = str(self.settings.serial_port or "").strip()
        return None if value.lower() in AUTO_SERIAL_VALUES else value

    @staticmethod
    def _auto_candidate_allowed(port: str) -> bool:
        lower = port.casefold()
        if lower.startswith("/dev/ttyama"):
            return False
        return not any(token in lower for token in AUTO_SKIP_TOKENS)

    @staticmethod
    def _deduplicate_ports(candidates: Iterable[str]) -> tuple[str, ...]:
        result: list[str] = []
        seen_paths: set[str] = set()
        for candidate in candidates:
            port = str(candidate or "").strip()
            if not port:
                continue
            try:
                identity = os.path.realpath(port)
            except OSError:
                identity = port
            identity = identity or port
            if identity in seen_paths:
                continue
            seen_paths.add(identity)
            result.append(port)
        return tuple(result)

    def _ports(self) -> tuple[str, ...]:
        configured = self._configured_port()
        if configured:
            # A fixed path is an explicit operator decision and is therefore used
            # exclusively. This prevents the app from probing unrelated Zigbee,
            # Z-Wave or console adapters on the same Home Assistant host.
            return (configured,)

        candidates: list[str] = []
        blocked_identities: set[str] = set()

        def identity(port: str) -> str:
            try:
                return os.path.realpath(port) or port
            except OSError:
                return port

        # Prefer stable by-id aliases. A recognisable Zigbee/Z-Wave alias also
        # blocks its /dev/ttyUSB* target so the same adapter cannot re-enter the
        # candidate list through a less descriptive path.
        for port in glob.glob("/dev/serial/by-id/*"):
            if self._auto_candidate_allowed(port):
                candidates.append(port)
            else:
                blocked_identities.add(identity(port))

        if list_ports is not None:
            for item in list_ports.comports():
                port = str(item.device)
                descriptor = " ".join(
                    str(getattr(item, field, "") or "")
                    for field in ("device", "name", "description", "manufacturer", "product", "interface", "hwid")
                )
                if self._auto_candidate_allowed(descriptor):
                    candidates.append(port)
                else:
                    blocked_identities.add(identity(port))

        for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*"):
            for port in glob.glob(pattern):
                if self._auto_candidate_allowed(port) and identity(port) not in blocked_identities:
                    candidates.append(port)
        return self._deduplicate_ports(candidates)

    @staticmethod
    def _classify_error(exc: Exception) -> str:
        text = str(exc).casefold()
        errno = getattr(exc, "errno", None)
        if errno == 16 or "resource busy" in text or "device or resource busy" in text:
            return "port_busy"
        if errno in {2, 19} or "no such file" in text or "no such device" in text:
            return "port_not_found"
        if errno in {13} or "permission denied" in text:
            return "permission_denied"
        if isinstance(exc, TimeoutError) or "no response to getver" in text or "returned no data" in text:
            return "no_response"
        if "getver did not identify radonscan" in text:
            return "wrong_device"
        return "read_error"

    @staticmethod
    def _read_until_idle(handle, *, deadline_seconds: float, maximum: int = 512) -> bytes:
        deadline = time.monotonic() + deadline_seconds
        data = bytearray()
        last_data = time.monotonic()
        while time.monotonic() < deadline and len(data) < maximum:
            chunk = handle.read(min(64, maximum - len(data)))
            if chunk:
                data.extend(chunk)
                last_data = time.monotonic()
            elif data and time.monotonic() - last_data > 0.12:
                break
        return bytes(data)

    @staticmethod
    def _read_exact(handle, length: int, timeout: float) -> bytes:
        deadline = time.monotonic() + timeout
        data = bytearray()
        while len(data) < length and time.monotonic() < deadline:
            chunk = handle.read(length - len(data))
            if chunk:
                data.extend(chunk)
        if len(data) != length:
            raise TimeoutError(f"expected {length} bytes, received {len(data)}")
        return bytes(data)

    def _read_block(self, handle, address: int) -> bytes:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                handle.reset_input_buffer()
                handle.write(build_spir_command(address, BLOCK_SIZE))
                handle.flush()
                data = self._read_exact(
                    handle,
                    BLOCK_SIZE,
                    max(5.0, self.settings.serial_timeout_seconds * 4),
                )
                if self.settings.diagnostic_logging:
                    LOGGER.debug(
                        "SPIR 0x%06X attempt=%s bytes=%s sha256=%s",
                        address,
                        attempt,
                        len(data),
                        hashlib.sha256(data).hexdigest(),
                    )
                return data
            except Exception as exc:
                last_error = exc
                LOGGER.warning(
                    "SPIR read failed at 0x%06X (attempt %s/3): %s",
                    address,
                    attempt,
                    exc,
                )
                time.sleep(0.15)
        raise RuntimeError(f"SPIR read failed at 0x{address:06X}: {last_error}")

    def _scan_port(self, port: str) -> ScanResult:
        detected_at = datetime.now(timezone.utc)
        if serial is None:
            return ScanResult(False, detected_at, port, None, None, None, None, "pyserial unavailable", (port,), "read_error")
        handle = None
        try:
            handle = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.15,
                write_timeout=2.0,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
            handle.dtr = False
            handle.rts = False
            handle.reset_input_buffer()
            handle.reset_output_buffer()
            handle.write(GETVER)
            handle.flush()
            version_payload = self._read_until_idle(
                handle, deadline_seconds=self.settings.serial_timeout_seconds, maximum=64
            )
            if not version_payload:
                raise TimeoutError("no response to GETVER")
            version = version_payload.decode("ascii", errors="ignore").strip("\x00\r\n ")
            if not version.startswith("RadonScan"):
                raise ValueError(f"GETVER did not identify RadonScan: {version_payload.hex()}")

            serial_payload = b""
            try:
                handle.reset_input_buffer()
                handle.write(GETSERIAL)
                handle.flush()
                serial_payload = self._read_until_idle(handle, deadline_seconds=1.0, maximum=32)
            except Exception:
                LOGGER.debug("GETSERIAL failed on %s", port, exc_info=True)

            blocks = [self._read_block(handle, address) for address in TARGET_ADDRESSES]
            snapshot = decode(*blocks, self.settings.factor_bq_m3_per_cph)
            model = "GQ RadonScan"
            firmware = version
            return ScanResult(
                True,
                detected_at,
                port,
                model,
                firmware,
                serial_number_text(serial_payload),
                snapshot,
                None,
                (port,),
                None,
            )
        except Exception as exc:
            return ScanResult(
                False,
                detected_at,
                port,
                None,
                None,
                None,
                None,
                str(exc),
                (port,),
                self._classify_error(exc),
            )
        finally:
            if handle is not None:
                try:
                    handle.close()
                except Exception:
                    pass

    def scan(self) -> ScanResult:
        ports = self._ports()
        configured = self._configured_port()
        if self.settings.diagnostic_logging:
            LOGGER.debug(
                "Serial candidates (%s mode): %s",
                "fixed" if configured else "automatic",
                list(ports),
            )
        if not ports:
            return ScanResult(
                False,
                datetime.now(timezone.utc),
                configured,
                None,
                None,
                None,
                None,
                "no eligible serial ports found",
                (),
                "no_ports",
            )

        # For a fixed port return the exact result so the UI can show a precise,
        # actionable status such as busy, missing, no response or wrong device.
        if configured:
            return self._scan_port(configured)

        errors: list[str] = []
        for port in ports:
            result = self._scan_port(port)
            if result.connected:
                return result
            errors.append(f"{port}: {result.error}")
        return ScanResult(
            False,
            datetime.now(timezone.utc),
            None,
            None,
            None,
            None,
            None,
            "; ".join(errors[-8:]),
            ports,
            "not_detected" if errors else "no_ports",
        )
