from datetime import datetime, timezone
from pathlib import Path

from radonscan3.decoder import HourlyRecord, Snapshot
from radonscan3.storage import Storage


def snapshot(*records: tuple[int, int], factor: float = 1.54) -> Snapshot:
    hourly = tuple(
        HourlyRecord(
            hour_index=index,
            time_seconds=index * 3600,
            raw_cph=raw,
            bq_m3=raw * factor,
        )
        for index, raw in records
    )
    return Snapshot(
        records=hourly,
        time_records=(),
        factor=factor,
        raw_start_offset=None,
        raw_end_offset=None,
        fd_value_0x270=0,
        hashes={},
    )


def prepare(tmp_path: Path) -> Storage:
    storage = Storage(tmp_path / "radonscan.sqlite3")
    storage.upsert_device(
        device_id="radon-1",
        model="GQ RadonScan",
        firmware="test",
        serial_number="serial",
        port="/dev/test",
        seen_at=datetime(2026, 7, 27, 9, 50, tzinfo=timezone.utc),
    )
    return storage


def test_delayed_poll_uses_hour_index_spacing(tmp_path: Path) -> None:
    storage = prepare(tmp_path)
    first = storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4)),
        detected_at=datetime(2026, 7, 27, 9, 50, tzinfo=timezone.utc),
        backfill=False,
    )
    assert first["inserted"] == 1

    second = storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4), (47, 3)),
        detected_at=datetime(2026, 7, 27, 11, 18, tzinfo=timezone.utc),
        backfill=True,
    )
    assert second["inserted"] == 1
    assert second["timestamp_source"] == "reconstructed_from_previous_hour_index"
    latest = storage.latest("radon-1")
    assert latest is not None
    assert latest["completed_at"] == "2026-07-27T10:50:00+00:00"


def test_new_zero_hour_requires_second_successful_read(tmp_path: Path) -> None:
    storage = prepare(tmp_path)
    storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4)),
        detected_at=datetime(2026, 7, 27, 9, 50, tzinfo=timezone.utc),
        backfill=False,
    )

    pending = storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4), (47, 0)),
        detected_at=datetime(2026, 7, 27, 11, 18, tzinfo=timezone.utc),
        backfill=True,
    )
    assert pending["inserted"] == 0
    assert pending["pending_zero_confirmation"] is True
    assert storage.latest("radon-1")["hour_index"] == 46

    confirmed = storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4), (47, 0)),
        detected_at=datetime(2026, 7, 27, 11, 28, tzinfo=timezone.utc),
        backfill=True,
    )
    assert confirmed["inserted"] == 1
    assert confirmed["pending_zero_confirmation"] is False
    latest = storage.latest("radon-1")
    assert latest["hour_index"] == 47
    assert latest["raw_cph"] == 0
    assert latest["completed_at"] == "2026-07-27T10:50:00+00:00"


def test_zero_followed_by_newer_index_is_not_lost(tmp_path: Path) -> None:
    storage = prepare(tmp_path)
    storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4)),
        detected_at=datetime(2026, 7, 27, 9, 50, tzinfo=timezone.utc),
        backfill=False,
    )
    storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4), (47, 0)),
        detected_at=datetime(2026, 7, 27, 11, 18, tzinfo=timezone.utc),
        backfill=True,
    )
    imported = storage.import_snapshot(
        device_id="radon-1",
        snapshot=snapshot((46, 4), (47, 0), (48, 2)),
        detected_at=datetime(2026, 7, 27, 12, 5, tzinfo=timezone.utc),
        backfill=True,
    )
    assert imported["inserted"] == 2
    rows = storage.history(device_id="radon-1", ascending=True)
    assert [(row["hour_index"], row["raw_cph"]) for row in rows] == [(46, 4), (47, 0), (48, 2)]


def test_existing_irregular_timestamps_are_repaired(tmp_path: Path) -> None:
    storage = prepare(tmp_path)
    with storage._connection() as con:
        con.execute(
            "INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)",
            ("radon-1", "2026-07-27T09:50:00+00:00", "test"),
        )
        campaign_id = con.execute("SELECT id FROM campaigns").fetchone()[0]
        for index, timestamp, raw in (
            (46, "2026-07-27T09:50:00+00:00", 4),
            (47, "2026-07-27T11:18:00+00:00", 0),
        ):
            con.execute(
                """
                INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                ("radon-1", campaign_id, index, timestamp, raw, raw * 1.54, 1.54, "test", timestamp),
            )
    result = storage.repair_measurement_timeline()
    assert result == {"updated_records": 1, "campaigns": 1}
    latest = storage.latest("radon-1")
    assert latest["completed_at"] == "2026-07-27T10:50:00+00:00"
