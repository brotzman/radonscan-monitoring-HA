import sqlite3
import tempfile
from pathlib import Path

from radonscan3.storage import Storage, SCHEMA_VERSION


def test_existing_measurements_survive_reopen_and_schema_check():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'existing.sqlite3'
        storage = Storage(path)
        with storage._connection() as con:
            con.execute("INSERT INTO devices VALUES(?,?,?,?,?,?,?)", ('device-1','GQ RadonScan','Re2.02','S1',None,'2026-01-01T00:00:00+00:00','2026-01-01T00:00:00+00:00'))
            con.execute("INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)", ('device-1','2026-01-01T00:00:00+00:00','regression'))
            campaign_id = con.execute('SELECT id FROM campaigns').fetchone()[0]
            con.execute("INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)", ('device-1',campaign_id,1,'2026-01-01T01:00:00+00:00',10,15.4,1.54,'device','2026-01-01T01:01:00+00:00'))
        reopened = Storage(path)
        with reopened._connection() as con:
            assert con.execute('SELECT COUNT(*) FROM measurements').fetchone()[0] == 1
            assert float(con.execute('SELECT factor FROM measurements').fetchone()[0]) == 1.54
            version = int(con.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0])
            assert version == SCHEMA_VERSION
