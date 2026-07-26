from datetime import datetime, timedelta, timezone

import pytest

from radonscan3.storage import Storage


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def test_overview_selection_uses_one_coherent_device_site_and_campaign(tmp_path):
    storage = Storage(tmp_path / "radon.sqlite3")
    start = datetime(2026, 7, 24, 0, 0, tzinfo=timezone.utc)

    with storage._connection() as con:
        for device_id in ("device-a", "device-b"):
            con.execute(
                "INSERT INTO devices(device_id,model,firmware,serial_number,last_port,first_seen,last_seen) VALUES(?,?,?,?,?,?,?)",
                (device_id, "GQ RadonScan", "2.02", device_id, "/dev/ttyUSB0", _iso(start), _iso(start + timedelta(hours=30))),
            )
        loc_a = con.execute("INSERT INTO locations(name,building,floor,active,created_at,updated_at) VALUES(?,?,?,1,?,?)", ("Keller", "Haus", "UG", _iso(start), _iso(start))).lastrowid
        loc_b = con.execute("INSERT INTO locations(name,building,floor,active,created_at,updated_at) VALUES(?,?,?,1,?,?)", ("Wohnzimmer", "Haus", "EG", _iso(start), _iso(start))).lastrowid
        campaign_a = con.execute("INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)", ("device-a", _iso(start), "test")).lastrowid
        campaign_b = con.execute("INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)", ("device-b", _iso(start), "test")).lastrowid

        selected_values = []
        for hour in range(24):
            value = 250.0 if hour == 12 else 50.0 + hour
            selected_values.append(value)
            completed = _iso(start + timedelta(hours=hour))
            con.execute(
                "INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at,location_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                ("device-a", campaign_a, hour + 1, completed, int(value / 1.54), value, 1.54, "test", completed, loc_a),
            )

        # Deliberately newer and much larger values outside the chosen site/device.
        for hour, (device_id, campaign_id, location_id, value) in enumerate(
            [
                ("device-a", campaign_a, loc_b, 900.0),
                ("device-b", campaign_b, loc_a, 1200.0),
            ],
            start=24,
        ):
            completed = _iso(start + timedelta(hours=hour))
            con.execute(
                "INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at,location_id) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (device_id, campaign_id, hour + 1, completed, int(value / 1.54), value, 1.54, "test", completed, location_id),
            )

    result = storage.overview_selection(
        minimum_coverage_percent=95,
        device_id="device-a",
        location_id=int(loc_a),
        campaign_id=int(campaign_a),
    )

    assert result["sample_count"] == 24
    assert result["latest"]["device_id"] == "device-a"
    assert result["latest"]["location_id"] == loc_a
    assert result["latest"]["campaign_id"] == campaign_a
    assert result["latest"]["bq_m3"] == selected_values[-1]

    period = result["statistics"]["24h"]
    assert period["available"] is True
    assert period["samples"] == 24
    assert period["coverage_percent"] == 100.0
    assert period["mean_bq_m3"] == pytest.approx(sum(selected_values) / len(selected_values))
    assert period["observed_maximum_bq_m3"] == 250.0
    assert period["observed_maximum_at"] == _iso(start + timedelta(hours=12))
    assert result["statistics"]["all"]["maximum_bq_m3"] == 250.0
