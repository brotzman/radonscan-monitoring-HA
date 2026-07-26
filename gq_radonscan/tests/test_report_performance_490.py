from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from radonscan3.config import Settings
from radonscan3.reports import ScientificReport
from radonscan3.storage import Storage


def _settings(tmp_path: Path, monkeypatch) -> Settings:
    options = tmp_path / "options.json"
    options.write_text(json.dumps({
        "factor_bq_m3_per_cph": 1.54,
        "analysis_timezone": "Europe/Berlin",
        "report_author": "Automated test",
    }))
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("WEB_PORT", "0")
    return Settings.load(options)


def test_three_year_compact_report_is_bounded_and_uses_all_records(tmp_path: Path, monkeypatch):
    settings = _settings(tmp_path, monkeypatch)
    storage = Storage(tmp_path / "radon.sqlite3")
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    hours = 3 * 365 * 24
    with storage._connection() as con:
        con.execute(
            "INSERT INTO devices(device_id,model,serial_number,firmware,last_port,first_seen,last_seen) VALUES(?,?,?,?,?,?,?)",
            ("d1", "GQ RadonScan", "S1", "RadonScan Re2.02", "/dev/ttyUSB0", start.isoformat(), (start + timedelta(hours=hours)).isoformat()),
        )
        con.execute("INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)", ("d1", start.isoformat(), "test"))
        campaign_id = con.execute("SELECT id FROM campaigns").fetchone()[0]
        batch = []
        for index in range(hours):
            completed = (start + timedelta(hours=index)).isoformat()
            raw = 40 + (index % 48)
            # Include periodic peaks so peak-preserving chart reduction is exercised.
            bq = float(raw) * 1.54 + (350.0 if index % 997 == 0 else 0.0)
            batch.append(("d1", campaign_id, index, completed, raw, bq, 1.54, "test", completed))
        con.executemany(
            "INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)",
            batch,
        )

    reporter = ScientificReport(storage, settings)
    started = time.perf_counter()
    result = reporter.create({"profile": "compact", "locale": "de", "device_id": "d1", "days": 3 * 365})
    elapsed = time.perf_counter() - started

    pdf_path = storage.reports_dir / result["filename"]
    assert pdf_path.is_file() and pdf_path.stat().st_size > 10_000
    assert pdf_path.stat().st_size < 5_000_000
    assert result["samples"] >= hours - 24
    assert result["chart_downsampled"] is True
    assert result["chart_points"] <= 1800
    assert elapsed < 15.0
