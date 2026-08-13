from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

from .protocol import BLOCK_SIZE

TIME_RECORD_SIZE = 14
RAW_END_OFFSET = 0x0CBC
DECODER_ID = "radonscan-re2-hourly-v3"


class DecodeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TimeRecord:
    sequence: int
    offset: int
    seconds: int
    hour_index: int
    payload_hex: str


@dataclass(frozen=True, slots=True)
class HourlyRecord:
    hour_index: int
    time_seconds: int
    raw_cph: int
    bq_m3: float


@dataclass(frozen=True, slots=True)
class Snapshot:
    records: tuple[HourlyRecord, ...]
    time_records: tuple[TimeRecord, ...]
    factor: float
    raw_start_offset: int | None
    raw_end_offset: int | None
    fd_value_0x270: int
    hashes: dict[str, str]

    @property
    def latest(self) -> HourlyRecord | None:
        return self.records[-1] if self.records else None

    def as_dict(self) -> dict[str, object]:
        latest = self.latest
        return {
            "decoder": DECODER_ID,
            "factor_bq_m3_per_cph": self.factor,
            "time_record_count": len(self.time_records),
            "hourly_record_count": len(self.records),
            "history_origin_marker_present": bool(self.time_records and self.time_records[0].seconds == 0),
            "history_window_start_hour_index": self.time_records[0].hour_index if self.time_records else None,
            "latest_hour_index": latest.hour_index if latest else None,
            "latest_time_seconds": latest.time_seconds if latest else None,
            "latest_raw_cph": latest.raw_cph if latest else None,
            "latest_bq_m3": latest.bq_m3 if latest else None,
            "raw_start_offset": self.raw_start_offset,
            "raw_end_offset": self.raw_end_offset,
            "fd_value_0x270": self.fd_value_0x270,
            "block_sha256": self.hashes,
        }


def _require_block(block: bytes, name: str) -> None:
    if len(block) != BLOCK_SIZE:
        raise DecodeError(f"{name} must be {BLOCK_SIZE} bytes, got {len(block)}")


def parse_time_records(block_fe: bytes) -> tuple[TimeRecord, ...]:
    _require_block(block_fe, "0x1FE000")
    records: list[TimeRecord] = []
    previous: int | None = None
    for offset in range(0, BLOCK_SIZE - TIME_RECORD_SIZE + 1, TIME_RECORD_SIZE):
        if block_fe[offset : offset + 2] != b"\xAA\x55":
            break
        seconds = int.from_bytes(block_fe[offset + 2 : offset + 6], "big")
        if seconds % 3600:
            raise DecodeError(f"time record at 0x{offset:03X} is not hour aligned")
        if previous is not None and seconds != previous + 3600:
            raise DecodeError(f"time sequence breaks at 0x{offset:03X}: {previous} -> {seconds}")
        records.append(
            TimeRecord(
                sequence=len(records),
                offset=offset,
                seconds=seconds,
                hour_index=seconds // 3600,
                payload_hex=block_fe[offset + 6 : offset + 14].hex(),
            )
        )
        previous = seconds
    if not records:
        raise DecodeError("0x1FE000 contains no AA55 time records")
    return tuple(records)


def _raw_values(block_fc: bytes, count: int) -> tuple[tuple[int, ...], int | None]:
    _require_block(block_fc, "0x1FC000")
    if count <= 0:
        return (), None
    start = RAW_END_OFFSET - (count - 1) * 4
    if start < 0 or RAW_END_OFFSET + 4 > BLOCK_SIZE:
        raise DecodeError("hourly history does not fit the observed raw-value region")
    values: list[int] = []
    for offset in range(start, RAW_END_OFFSET + 1, 4):
        value = struct.unpack_from("<I", block_fc, offset)[0]
        if value > 10_000_000:
            raise DecodeError(f"implausible CPH value {value} at 0x{offset:03X}")
        values.append(value)
    return tuple(values), start


def decode(block_fc: bytes, block_fd: bytes, block_fe: bytes, factor: float) -> Snapshot:
    _require_block(block_fd, "0x1FD000")
    factor = float(factor)
    if not 0.001 <= factor <= 1000:
        raise DecodeError("conversion factor outside supported range")
    time_records = parse_time_records(block_fe)

    # Fresh RadonScan histories begin with a special t=0 marker that has no
    # corresponding CPH value. Field devices can outlive the 14-byte history
    # window, however, and then present a continuous hour-aligned window whose
    # first visible record is greater than zero. In that rolling-window state
    # every visible time record represents a completed hourly measurement.
    #
    # Keep the original marker behaviour byte-for-byte compatible while also
    # accepting a non-zero start only after parse_time_records() has verified
    # strict +3600-second continuity for the complete visible window.
    origin_marker_present = time_records[0].seconds == 0
    measurement_time_records = time_records[1:] if origin_marker_present else time_records
    raw_values, raw_start = _raw_values(block_fc, len(measurement_time_records))
    records = tuple(
        HourlyRecord(
            hour_index=time_record.hour_index,
            time_seconds=time_record.seconds,
            raw_cph=int(raw),
            bq_m3=round(float(raw) * factor, 6),
        )
        for time_record, raw in zip(measurement_time_records, raw_values)
    )
    return Snapshot(
        records=records,
        time_records=time_records,
        factor=factor,
        raw_start_offset=raw_start,
        raw_end_offset=RAW_END_OFFSET if records else None,
        fd_value_0x270=struct.unpack_from("<I", block_fd, 0x270)[0],
        hashes={
            "0x1FC000": hashlib.sha256(block_fc).hexdigest(),
            "0x1FD000": hashlib.sha256(block_fd).hexdigest(),
            "0x1FE000": hashlib.sha256(block_fe).hexdigest(),
        },
    )
