from __future__ import annotations

from datetime import datetime, timedelta, timezone
import struct

import pytest

from radonscan3.decoder import DecodeError, RAW_END_OFFSET, TIME_RECORD_SIZE, decode, parse_time_records
from radonscan3.protocol import BLOCK_SIZE
from radonscan3.storage import Storage


def _time_block(hour_indexes: list[int]) -> bytes:
    block = bytearray(BLOCK_SIZE)
    for position, hour_index in enumerate(hour_indexes):
        offset = position * TIME_RECORD_SIZE
        block[offset : offset + 2] = b"\xAA\x55"
        block[offset + 2 : offset + 6] = int(hour_index * 3600).to_bytes(4, "big")
        block[offset + 6 : offset + 14] = bytes([position % 251]) * 8
    return bytes(block)


def _raw_block(values: list[int]) -> bytes:
    block = bytearray(BLOCK_SIZE)
    if values:
        start = RAW_END_OFFSET - (len(values) - 1) * 4
        for position, value in enumerate(values):
            struct.pack_into("<I", block, start + position * 4, value)
    return bytes(block)


def _fd_block() -> bytes:
    return bytes(BLOCK_SIZE)


def _snapshot(hour_indexes: list[int], raw_values: list[int]):
    return decode(_raw_block(raw_values), _fd_block(), _time_block(hour_indexes), 1.53)


def test_fresh_history_keeps_t0_marker_semantics() -> None:
    snapshot = _snapshot([0, 1, 2, 3], [11, 22, 33])
    assert [item.hour_index for item in snapshot.records] == [1, 2, 3]
    assert [item.raw_cph for item in snapshot.records] == [11, 22, 33]
    assert snapshot.as_dict()["history_origin_marker_present"] is True
    assert snapshot.as_dict()["history_window_start_hour_index"] == 0


def test_continuous_nonzero_history_window_is_accepted() -> None:
    snapshot = _snapshot([292, 293, 294], [41, 42, 43])
    assert [item.hour_index for item in snapshot.records] == [292, 293, 294]
    assert [item.raw_cph for item in snapshot.records] == [41, 42, 43]
    assert snapshot.as_dict()["history_origin_marker_present"] is False
    assert snapshot.as_dict()["history_window_start_hour_index"] == 292


def test_full_292_record_rolling_window_fits_raw_region() -> None:
    hours = list(range(500, 792))
    values = list(range(1, 293))
    snapshot = _snapshot(hours, values)
    assert len(snapshot.time_records) == 292
    assert len(snapshot.records) == 292
    assert snapshot.records[0].hour_index == 500
    assert snapshot.records[0].raw_cph == 1
    assert snapshot.records[-1].hour_index == 791
    assert snapshot.records[-1].raw_cph == 292
    assert snapshot.raw_start_offset == 0x830


def test_nonzero_window_still_requires_hour_alignment() -> None:
    block = bytearray(_time_block([10, 11]))
    block[2:6] = int(10 * 3600 + 1).to_bytes(4, "big")
    with pytest.raises(DecodeError, match="not hour aligned"):
        parse_time_records(bytes(block))


def test_nonzero_window_still_requires_exact_hour_sequence() -> None:
    with pytest.raises(DecodeError, match="time sequence breaks"):
        parse_time_records(_time_block([10, 12]))


def test_rolling_window_continues_existing_campaign(tmp_path) -> None:
    storage = Storage(tmp_path / "radonscan.sqlite3")
    detected_at = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    storage.upsert_device(
        device_id="radon-1",
        model="GQ RadonScan",
        firmware="test",
        serial_number="serial",
        port="/dev/test",
        seen_at=detected_at,
    )

    fresh = _snapshot([0, 1, 2, 3, 4], [1, 2, 3, 4])
    first = storage.import_snapshot(
        device_id="radon-1",
        snapshot=fresh,
        detected_at=detected_at,
        backfill=True,
        confirm_latest_zero=False,
    )
    assert first["inserted"] == 4
    assert first["campaign_reset"] is False

    rolling = _snapshot([5, 6, 7], [5, 6, 7])
    second = storage.import_snapshot(
        device_id="radon-1",
        snapshot=rolling,
        detected_at=detected_at + timedelta(hours=3),
        backfill=True,
        confirm_latest_zero=False,
    )
    assert second["inserted"] == 3
    assert second["campaign_reset"] is False
    assert second["latest_hour_index"] == 7
    rows = storage.history(device_id="radon-1", ascending=True)
    assert [(row["hour_index"], row["raw_cph"]) for row in rows] == [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6),
        (7, 7),
    ]
