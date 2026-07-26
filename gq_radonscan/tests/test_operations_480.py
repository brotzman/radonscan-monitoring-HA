from __future__ import annotations

import sqlite3
from pathlib import Path

from radonscan3.storage import Storage


def test_complete_reset_returns_verifiable_report(tmp_path: Path):
    storage = Storage(tmp_path / "radon.sqlite3")
    with sqlite3.connect(storage.path) as con:
        con.execute("INSERT INTO devices(device_id,model,serial_number,firmware,first_seen,last_seen) VALUES(?,?,?,?,?,?)", ("d1","RadonScan","1","2.02","2026-01-01T00:00:00Z","2026-01-01T00:00:00Z"))
        con.execute("INSERT INTO campaigns(device_id,started_at,reason) VALUES(?,?,?)", ("d1","2026-01-01T00:00:00Z","test"))
        campaign_id=con.execute("SELECT id FROM campaigns").fetchone()[0]
        con.execute("INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)", ("d1",campaign_id,1,"2026-01-01T01:00:00Z",10,15.4,1.54,"spir","2026-01-01T01:00:00Z"))
        con.commit()
    result=storage.reset_all_data()
    assert result["database_reset"] is True
    assert result["deleted_measurements"] == 1
    assert result["deleted_total_records"] >= 3
    assert result["integrity"] == "ok"
    assert result["backup"].startswith("before-complete-reset-")
    assert (storage.backups_dir / result["backup"]).is_file()
    with sqlite3.connect(storage.path) as con:
        assert con.execute("SELECT COUNT(*) FROM measurements").fetchone()[0] == 0
        assert con.execute("SELECT value_json FROM runtime WHERE key='skip_history_backfill_once'").fetchone()[0] == "true"


def test_standard_pytest_configuration_exists():
    root=Path(__file__).resolve().parents[1]
    assert (root / "pyproject.toml").is_file()
    assert 'pythonpath = ["rootfs/usr/local/lib"]' in (root / "pyproject.toml").read_text()
