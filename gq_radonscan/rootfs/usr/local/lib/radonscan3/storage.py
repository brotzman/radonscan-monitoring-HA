from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import csv
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
from typing import Iterable
import zipfile

from .analysis import analyse_records, iso as analysis_iso, parse_dt, window_summary
from .decoder import Snapshot

SCHEMA_VERSION = 8


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


class StorageError(RuntimeError):
    pass


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.path.parent
        self.maps_dir = self.data_dir / "maps"
        self.reports_dir = self.data_dir / "reports"
        self.backups_dir = self.data_dir / "backups"
        for directory in (self.maps_dir, self.reports_dir, self.backups_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    @contextmanager
    def _connection(self):
        with self._lock:
            con = sqlite3.connect(self.path, timeout=20)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA busy_timeout=20000")
            try:
                yield con
                con.commit()
            except Exception:
                con.rollback()
                raise
            finally:
                con.close()

    @staticmethod
    def _column_exists(con: sqlite3.Connection, table: str, column: str) -> bool:
        return any(row[1] == column for row in con.execute(f"PRAGMA table_info({table})"))

    def _init_schema(self) -> None:
        with self._connection() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    firmware TEXT,
                    serial_number TEXT,
                    last_port TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id)
                );
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    campaign_id INTEGER NOT NULL,
                    hour_index INTEGER NOT NULL,
                    completed_at TEXT NOT NULL,
                    raw_cph INTEGER NOT NULL,
                    bq_m3 REAL NOT NULL,
                    factor REAL NOT NULL,
                    source TEXT NOT NULL,
                    inserted_at TEXT NOT NULL,
                    UNIQUE(device_id, campaign_id, hour_index),
                    FOREIGN KEY(device_id) REFERENCES devices(device_id),
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                );
                CREATE INDEX IF NOT EXISTS idx_measurements_completed
                    ON measurements(completed_at DESC);
                CREATE INDEX IF NOT EXISTS idx_measurements_campaign
                    ON measurements(device_id, campaign_id, hour_index);
                CREATE TABLE IF NOT EXISTS runtime (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS maps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    building TEXT,
                    floor TEXT,
                    filename TEXT NOT NULL UNIQUE,
                    original_filename TEXT,
                    mime_type TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    uploaded_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    building TEXT,
                    floor TEXT,
                    room_type TEXT,
                    map_id INTEGER,
                    x_percent REAL,
                    y_percent REAL,
                    measurement_height_m REAL,
                    notes TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(map_id) REFERENCES maps(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    campaign_id INTEGER,
                    location_id INTEGER,
                    title TEXT NOT NULL,
                    purpose TEXT,
                    responsible TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id) ON DELETE SET NULL,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL,
                    FOREIGN KEY(location_id) REFERENCES locations(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    location_id INTEGER,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE SET NULL,
                    FOREIGN KEY(location_id) REFERENCES locations(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL UNIQUE,
                    profile TEXT NOT NULL,
                    locale TEXT NOT NULL,
                    title TEXT NOT NULL,
                    period_start TEXT,
                    period_end TEXT,
                    location_id INTEGER,
                    filename TEXT NOT NULL UNIQUE,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(location_id) REFERENCES locations(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    target TEXT,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    user_name TEXT
                );
                CREATE TABLE IF NOT EXISTS worldmap_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempted_at TEXT NOT NULL,
                    measurement_at TEXT,
                    bq_m3 REAL,
                    pci_l REAL,
                    trigger TEXT NOT NULL,
                    ok INTEGER NOT NULL,
                    http_status INTEGER,
                    response TEXT,
                    user_name TEXT
                );
                CREATE TABLE IF NOT EXISTS worldmap_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    measurement_id INTEGER NOT NULL UNIQUE,
                    measurement_at TEXT NOT NULL,
                    bq_m3 REAL NOT NULL,
                    pci_l REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt_at TEXT,
                    last_attempt_at TEXT,
                    last_error TEXT,
                    uploaded_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(measurement_id) REFERENCES measurements(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_worldmap_queue_status ON worldmap_queue(status,next_attempt_at,measurement_at);
                CREATE TABLE IF NOT EXISTS factor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    factor REAL NOT NULL,
                    source TEXT NOT NULL,
                    effective_at TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS calibrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    calibrated_at TEXT NOT NULL,
                    laboratory TEXT,
                    certificate_reference TEXT,
                    factor REAL,
                    relative_uncertainty_percent REAL,
                    next_due_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_calibrations_device ON calibrations(device_id,calibrated_at DESC);
                CREATE TABLE IF NOT EXISTS campaign_protocols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL UNIQUE,
                    research_question TEXT,
                    room_description TEXT,
                    placement_description TEXT,
                    distance_floor_m REAL,
                    distance_wall_m REAL,
                    ventilation_conditions TEXT,
                    planned_end_at TEXT,
                    responsible TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
                );
                                CREATE INDEX IF NOT EXISTS idx_factor_history_device ON factor_history(device_id,effective_at DESC);
                CREATE INDEX IF NOT EXISTS idx_worldmap_uploads_time ON worldmap_uploads(attempted_at DESC);
                CREATE INDEX IF NOT EXISTS idx_sessions_period ON sessions(started_at, ended_at);
                CREATE INDEX IF NOT EXISTS idx_events_time ON events(occurred_at DESC);
                CREATE INDEX IF NOT EXISTS idx_locations_map ON locations(map_id);
                """
            )
            if not self._column_exists(con, "measurements", "location_id"):
                con.execute("ALTER TABLE measurements ADD COLUMN location_id INTEGER")
            if not self._column_exists(con, "measurements", "session_id"):
                con.execute("ALTER TABLE measurements ADD COLUMN session_id INTEGER")
            con.execute("CREATE INDEX IF NOT EXISTS idx_measurements_location ON measurements(location_id, completed_at)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_measurements_session ON measurements(session_id, completed_at)")
            con.execute(
                "INSERT INTO metadata(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(SCHEMA_VERSION),),
            )


    def record_worldmap_upload(self, result: dict[str, object], *, user_name: str | None = None) -> None:
        with self._connection() as con:
            con.execute(
                "INSERT INTO worldmap_uploads(attempted_at,measurement_at,bq_m3,pci_l,trigger,ok,http_status,response,user_name) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    str(result.get("attempted_at") or iso(utc_now())),
                    result.get("measurement_at"),
                    result.get("bq_m3"),
                    result.get("pci_l"),
                    str(result.get("trigger") or "manual"),
                    1 if result.get("ok") else 0,
                    result.get("http_status"),
                    str(result.get("response") or "")[:2000],
                    user_name,
                ),
            )

    def worldmap_uploads(self, limit: int = 100) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT * FROM worldmap_uploads ORDER BY attempted_at DESC,id DESC LIMIT ?",
                (max(1, min(1000, int(limit))),),
            ).fetchall()
        return [dict(row) for row in rows]

    def queue_worldmap_measurements(self, *, max_age_hours: int = 72) -> int:
        cutoff = iso(utc_now() - timedelta(hours=max(1, int(max_age_hours))))
        now = iso(utc_now())
        with self._connection() as con:
            cur = con.execute(
                "INSERT OR IGNORE INTO worldmap_queue(measurement_id,measurement_at,bq_m3,pci_l,status,created_at) "
                "SELECT id,completed_at,bq_m3,bq_m3/37.0,'pending',? FROM measurements WHERE completed_at>=?",
                (now, cutoff),
            )
            return int(cur.rowcount)

    def next_worldmap_item(self) -> dict[str, object] | None:
        now = iso(utc_now())
        with self._connection() as con:
            row = con.execute(
                "SELECT * FROM worldmap_queue WHERE status IN ('pending','retry') "
                "AND (next_attempt_at IS NULL OR next_attempt_at<=?) ORDER BY measurement_at,id LIMIT 1",
                (now,),
            ).fetchone()
        return dict(row) if row else None

    def update_worldmap_item(self, queue_id: int, *, ok: bool, error: str | None = None, retry_limit: int = 8) -> None:
        now_dt = utc_now()
        now = iso(now_dt)
        with self._connection() as con:
            row = con.execute("SELECT attempts FROM worldmap_queue WHERE id=?", (queue_id,)).fetchone()
            if not row:
                return
            attempts = int(row['attempts']) + 1
            if ok:
                con.execute(
                    "UPDATE worldmap_queue SET status='uploaded',attempts=?,last_attempt_at=?,last_error=NULL,uploaded_at=?,next_attempt_at=NULL WHERE id=?",
                    (attempts, now, now, queue_id),
                )
            else:
                terminal = attempts >= max(1, int(retry_limit))
                delay_minutes = min(24 * 60, 5 * (2 ** min(attempts - 1, 8)))
                next_at = iso(now_dt + timedelta(minutes=delay_minutes))
                con.execute(
                    "UPDATE worldmap_queue SET status=?,attempts=?,last_attempt_at=?,last_error=?,next_attempt_at=? WHERE id=?",
                    ('failed' if terminal else 'retry', attempts, now, str(error or '')[:1000], None if terminal else next_at, queue_id),
                )

    def worldmap_queue_summary(self) -> dict[str, object]:
        with self._connection() as con:
            rows = con.execute("SELECT status,COUNT(*) AS count FROM worldmap_queue GROUP BY status").fetchall()
            oldest = con.execute("SELECT measurement_at FROM worldmap_queue WHERE status IN ('pending','retry') ORDER BY measurement_at LIMIT 1").fetchone()
        counts = {str(row['status']): int(row['count']) for row in rows}
        return {
            'counts': counts,
            'pending_total': counts.get('pending', 0) + counts.get('retry', 0),
            'oldest_pending': oldest['measurement_at'] if oldest else None,
        }

    def retry_worldmap_failures(self) -> int:
        with self._connection() as con:
            cur = con.execute("UPDATE worldmap_queue SET status='retry',next_attempt_at=NULL,last_error=NULL WHERE status='failed'")
            return int(cur.rowcount)

    def record_factor_configuration(self, factor: float, *, device_id: str | None = None, source: str = 'configuration', note: str | None = None) -> bool:
        now = iso(utc_now())
        with self._connection() as con:
            row = con.execute(
                "SELECT factor FROM factor_history WHERE COALESCE(device_id,'')=COALESCE(?,'') ORDER BY effective_at DESC,id DESC LIMIT 1",
                (device_id,),
            ).fetchone()
            if row and abs(float(row['factor']) - float(factor)) < 1e-12:
                return False
            con.execute(
                "INSERT INTO factor_history(device_id,factor,source,effective_at,note,created_at) VALUES(?,?,?,?,?,?)",
                (device_id, float(factor), source, now, note, now),
            )
        self.audit('factor_change', f'device:{device_id or "default"}', {'factor': factor, 'source': source, 'note': note})
        return True

    def factor_history(self, device_id: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        with self._connection() as con:
            if device_id:
                rows = con.execute("SELECT * FROM factor_history WHERE device_id=? ORDER BY effective_at DESC,id DESC LIMIT ?", (device_id, max(1,min(1000,int(limit))))).fetchall()
            else:
                rows = con.execute("SELECT * FROM factor_history ORDER BY effective_at DESC,id DESC LIMIT ?", (max(1,min(1000,int(limit))),)).fetchall()
        return [dict(row) for row in rows]

    def set_runtime(self, key: str, value: object) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
        with self._connection() as con:
            con.execute(
                "INSERT INTO runtime(key,value_json,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at",
                (key, payload, iso(utc_now())),
            )

    def get_runtime(self, key: str, default: object = None) -> object:
        with self._connection() as con:
            row = con.execute("SELECT value_json FROM runtime WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value_json"])
        except Exception:
            return default

    def runtime_all(self) -> dict[str, object]:
        with self._connection() as con:
            rows = con.execute("SELECT key,value_json FROM runtime").fetchall()
        result: dict[str, object] = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value_json"])
            except Exception:
                result[row["key"]] = None
        return result

    def upsert_device(
        self,
        *,
        device_id: str,
        model: str,
        firmware: str | None,
        serial_number: str | None,
        port: str | None,
        seen_at: datetime,
    ) -> None:
        now = iso(seen_at)
        with self._connection() as con:
            con.execute(
                """
                INSERT INTO devices(device_id,model,firmware,serial_number,last_port,first_seen,last_seen)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(device_id) DO UPDATE SET
                    model=excluded.model,
                    firmware=excluded.firmware,
                    serial_number=excluded.serial_number,
                    last_port=excluded.last_port,
                    last_seen=excluded.last_seen
                """,
                (device_id, model, firmware, serial_number, port, now, now),
            )

    def _active_campaign(self, con: sqlite3.Connection, device_id: str) -> sqlite3.Row | None:
        return con.execute(
            "SELECT * FROM campaigns WHERE device_id=? AND active=1 ORDER BY id DESC LIMIT 1",
            (device_id,),
        ).fetchone()

    def _new_campaign(self, con: sqlite3.Connection, device_id: str, started_at: datetime, reason: str) -> int:
        con.execute("UPDATE campaigns SET active=0 WHERE device_id=?", (device_id,))
        cur = con.execute(
            "INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)",
            (device_id, iso(started_at), reason),
        )
        return int(cur.lastrowid)

    @staticmethod
    def _session_for_time(con: sqlite3.Connection, device_id: str, completed_at: str) -> sqlite3.Row | None:
        return con.execute(
            """
            SELECT * FROM sessions
            WHERE (device_id=? OR device_id IS NULL)
              AND started_at <= ?
              AND (ended_at IS NULL OR ended_at >= ?)
            ORDER BY CASE WHEN device_id=? THEN 0 ELSE 1 END, started_at DESC, id DESC
            LIMIT 1
            """,
            (device_id, completed_at, completed_at, device_id),
        ).fetchone()

    def import_snapshot(
        self,
        *,
        device_id: str,
        snapshot: Snapshot,
        detected_at: datetime,
        backfill: bool,
    ) -> dict[str, object]:
        latest = snapshot.latest
        if latest is None:
            return {"inserted": 0, "campaign_reset": False, "latest_hour_index": None}

        inserted = 0
        reset = False
        with self._connection() as con:
            campaign = self._active_campaign(con, device_id)
            if campaign is None:
                campaign_id = self._new_campaign(con, device_id, detected_at, "first_history")
                last_index = None
            else:
                campaign_id = int(campaign["id"])
                row = con.execute(
                    "SELECT MAX(hour_index) AS idx FROM measurements WHERE device_id=? AND campaign_id=?",
                    (device_id, campaign_id),
                ).fetchone()
                last_index = row["idx"] if row else None

            if last_index is not None and latest.hour_index < int(last_index):
                campaign_id = self._new_campaign(con, device_id, detected_at, "device_history_reset")
                last_index = None
                reset = True

            if last_index is None:
                candidates = snapshot.records if backfill else (latest,)
            else:
                candidates = tuple(record for record in snapshot.records if record.hour_index > int(last_index))

            for record in candidates:
                age = latest.hour_index - record.hour_index
                completed_at_dt = detected_at - timedelta(hours=max(0, age))
                completed_at = iso(completed_at_dt)
                session = self._session_for_time(con, device_id, completed_at)
                location_id = int(session["location_id"]) if session and session["location_id"] is not None else None
                session_id = int(session["id"]) if session else None
                cur = con.execute(
                    """
                    INSERT OR IGNORE INTO measurements(
                        device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at,
                        location_id,session_id
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        device_id,
                        campaign_id,
                        record.hour_index,
                        completed_at,
                        record.raw_cph,
                        record.bq_m3,
                        snapshot.factor,
                        "spir_hourly_history",
                        iso(utc_now()),
                        location_id,
                        session_id,
                    ),
                )
                inserted += int(cur.rowcount > 0)

        return {
            "inserted": inserted,
            "campaign_reset": reset,
            "latest_hour_index": latest.hour_index,
            "latest_raw_cph": latest.raw_cph,
            "latest_bq_m3": latest.bq_m3,
        }

    def prune(self, retention_days: int) -> int:
        cutoff = iso(utc_now() - timedelta(days=int(retention_days)))
        with self._connection() as con:
            cur = con.execute("DELETE FROM measurements WHERE completed_at < ?", (cutoff,))
            return int(cur.rowcount)

    @staticmethod
    def _measurement_select() -> str:
        return """
            SELECT m.*, d.model, d.firmware, d.serial_number, d.last_port,
                   l.name AS location_name, l.building AS location_building,
                   l.floor AS location_floor, s.title AS session_title
            FROM measurements m
            JOIN devices d ON d.device_id=m.device_id
            LEFT JOIN locations l ON l.id=m.location_id
            LEFT JOIN sessions s ON s.id=m.session_id
        """

    def latest(self, device_id: str | None = None) -> dict[str, object] | None:
        where = " WHERE m.device_id=?" if device_id else ""
        params: tuple[object, ...] = (str(device_id),) if device_id else ()
        with self._connection() as con:
            row = con.execute(
                self._measurement_select() + where + " ORDER BY m.completed_at DESC, m.id DESC LIMIT 1",
                params,
            ).fetchone()
        return dict(row) if row else None

    def device(self, device_id: str | None = None) -> dict[str, object] | None:
        with self._connection() as con:
            if device_id:
                row = con.execute("SELECT * FROM devices WHERE device_id=?", (device_id,)).fetchone()
            else:
                row = con.execute("SELECT * FROM devices ORDER BY last_seen DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def devices(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute("SELECT * FROM devices ORDER BY last_seen DESC").fetchall()
        return [dict(row) for row in rows]

    def campaigns(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                """
                SELECT c.*, COUNT(m.id) AS sample_count, MIN(m.completed_at) AS first_measurement,
                       MAX(m.completed_at) AS last_measurement
                FROM campaigns c LEFT JOIN measurements m ON m.campaign_id=c.id
                GROUP BY c.id ORDER BY c.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self, device_id: str | None = None) -> int:
        with self._connection() as con:
            if device_id:
                return int(con.execute("SELECT COUNT(*) FROM measurements WHERE device_id=?", (device_id,)).fetchone()[0])
            return int(con.execute("SELECT COUNT(*) FROM measurements").fetchone()[0])

    def history(
        self,
        *,
        limit: int = 500,
        days: int | None = None,
        start: str | None = None,
        end: str | None = None,
        location_id: int | None = None,
        campaign_id: int | None = None,
        device_id: str | None = None,
        ascending: bool = False,
    ) -> list[dict[str, object]]:
        clauses: list[str] = []
        params: list[object] = []
        if days is not None and not start:
            clauses.append("m.completed_at >= ?")
            params.append(iso(utc_now() - timedelta(days=max(1, int(days)))))
        if start:
            dt = parse_dt(start)
            if dt:
                clauses.append("m.completed_at >= ?")
                params.append(analysis_iso(dt))
        if end:
            dt = parse_dt(end)
            if dt:
                clauses.append("m.completed_at <= ?")
                params.append(analysis_iso(dt))
        if location_id is not None:
            clauses.append("m.location_id=?")
            params.append(int(location_id))
        if campaign_id is not None:
            clauses.append("m.campaign_id=?")
            params.append(int(campaign_id))
        if device_id:
            clauses.append("m.device_id=?")
            params.append(str(device_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(max(1, min(100000, int(limit))))
        direction = "ASC" if ascending else "DESC"
        with self._connection() as con:
            rows = con.execute(
                self._measurement_select() + where + f" ORDER BY m.completed_at {direction}, m.id {direction} LIMIT ?",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _active_campaign_id(con: sqlite3.Connection, device_id: str | None = None) -> int | None:
        if device_id:
            row = con.execute(
                "SELECT id FROM campaigns WHERE active=1 AND device_id=? ORDER BY started_at DESC, id DESC LIMIT 1",
                (device_id,),
            ).fetchone()
        else:
            row = con.execute(
                "SELECT id FROM campaigns WHERE active=1 ORDER BY started_at DESC, id DESC LIMIT 1"
            ).fetchone()
        return int(row["id"]) if row else None

    def _active_campaign_records(self, device_id: str | None = None) -> list[dict[str, object]]:
        with self._connection() as con:
            if device_id is None:
                latest = con.execute(
                    "SELECT device_id FROM measurements ORDER BY completed_at DESC,id DESC LIMIT 1"
                ).fetchone()
                device_id = str(latest["device_id"]) if latest else None
            campaign_id = self._active_campaign_id(con, device_id)
            if campaign_id is None:
                return []
            rows = con.execute(
                "SELECT completed_at,bq_m3,raw_cph,hour_index,factor,device_id,campaign_id,location_id,session_id "
                "FROM measurements WHERE campaign_id=? ORDER BY completed_at",
                (campaign_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def average(
        self,
        hours: int | None,
        minimum_coverage_percent: float = 95.0,
        device_id: str | None = None,
    ) -> dict[str, object]:
        records = self._active_campaign_records(device_id)
        if hours is None:
            result = analyse_records(records, minimum_coverage_percent=minimum_coverage_percent)["statistics"]
            return {
                "available": bool(result["samples"]),
                "reason": None if result["samples"] else "no_data",
                "mean_bq_m3": result["mean_bq_m3"],
                "minimum_bq_m3": result["minimum_bq_m3"],
                "maximum_bq_m3": result["maximum_bq_m3"],
                "median_bq_m3": result["median_bq_m3"],
                "samples": result["samples"],
                "required_samples": None,
                "missing_samples": 0,
                "coverage_percent": 100.0 if result["samples"] else 0.0,
                "period_start": result["actual_start"],
                "period_end": result["actual_end"],
                "data_span_hours": result["data_span_hours"],
                "quality": result["quality"],
            }
        latest = max((parse_dt(row.get("completed_at")) for row in records), default=None)
        return window_summary(
            records,
            hours=int(hours),
            end=latest,
            minimum_coverage_percent=minimum_coverage_percent,
        )

    def stats(
        self, minimum_coverage_percent: float = 95.0, device_id: str | None = None
    ) -> dict[str, object]:
        return {
            "24h": self.average(24, minimum_coverage_percent, device_id),
            "7d": self.average(168, minimum_coverage_percent, device_id),
            "30d": self.average(720, minimum_coverage_percent, device_id),
            "all": self.average(None, minimum_coverage_percent, device_id),
        }

    def analysis(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        days: int | None = 30,
        location_id: int | None = None,
        campaign_id: int | None = None,
        device_id: str | None = None,
        warning_threshold: float = 100.0,
        danger_threshold: float = 300.0,
        minimum_coverage_percent: float = 95.0,
        timezone_name: str = "UTC",
    ) -> dict[str, object]:
        latest = self.latest(device_id=device_id)
        end_dt = parse_dt(end) if end else parse_dt(latest.get("completed_at")) if latest else utc_now()
        start_dt = parse_dt(start) if start else (end_dt - timedelta(days=max(1, int(days or 30))) if end_dt and days else None)
        records = self.history(
            limit=100000,
            start=analysis_iso(start_dt) if start_dt else None,
            end=analysis_iso(end_dt) if end_dt else None,
            location_id=location_id,
            campaign_id=campaign_id,
            device_id=device_id,
            ascending=True,
        )
        result = analyse_records(
            records,
            start=start_dt,
            end=end_dt,
            warning_threshold=warning_threshold,
            danger_threshold=danger_threshold,
            minimum_coverage_percent=minimum_coverage_percent,
            timezone_name=timezone_name,
        )
        result["selection"] = {
            "start": analysis_iso(start_dt),
            "end": analysis_iso(end_dt),
            "days": days,
            "location_id": location_id,
            "campaign_id": campaign_id,
            "device_id": device_id,
            "timezone": timezone_name,
        }
        result["events"] = self.events(start=analysis_iso(start_dt), end=analysis_iso(end_dt), location_id=location_id)
        return result

    def csv_bytes(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        location_id: int | None = None,
        device_id: str | None = None,
    ) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "completed_at_utc",
                "hour_index",
                "raw_cph",
                "bq_m3",
                "factor",
                "device_id",
                "campaign_id",
                "location",
                "location_id",
                "session_id",
                "source",
            ]
        )
        rows = self.history(
            limit=100000,
            start=start,
            end=end,
            location_id=location_id,
            device_id=device_id,
            ascending=True,
        )
        for row in rows:
            writer.writerow(
                [
                    row["completed_at"],
                    row["hour_index"],
                    row["raw_cph"],
                    f"{float(row['bq_m3']):.6f}",
                    f"{float(row['factor']):.6f}",
                    row["device_id"],
                    row["campaign_id"],
                    row.get("location_name") or "",
                    row.get("location_id") or "",
                    row.get("session_id") or "",
                    row["source"],
                ]
            )
        return output.getvalue().encode("utf-8-sig")

    # Maps and locations -------------------------------------------------
    def add_map(
        self,
        *,
        name: str,
        building: str,
        floor: str,
        filename: str,
        original_filename: str,
        mime_type: str,
        width: int | None,
        height: int | None,
    ) -> dict[str, object]:
        now = iso(utc_now())
        with self._connection() as con:
            cur = con.execute(
                "INSERT INTO maps(name,building,floor,filename,original_filename,mime_type,width,height,uploaded_at) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (name, building, floor, filename, original_filename, mime_type, width, height, now),
            )
            map_id = int(cur.lastrowid)
        self.audit("map_upload", f"map:{map_id}", {"name": name, "filename": filename})
        return self.map(map_id) or {}

    def maps(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                """
                SELECT mp.*, COUNT(l.id) AS location_count
                FROM maps mp LEFT JOIN locations l ON l.map_id=mp.id
                GROUP BY mp.id ORDER BY mp.uploaded_at DESC, mp.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def map(self, map_id: int) -> dict[str, object] | None:
        with self._connection() as con:
            row = con.execute("SELECT * FROM maps WHERE id=?", (int(map_id),)).fetchone()
        return dict(row) if row else None

    def delete_map(self, map_id: int, *, delete_locations: bool = False, user_name: str | None = None) -> int:
        item = self.map(map_id)
        if not item:
            return 0
        with self._connection() as con:
            if delete_locations:
                con.execute("UPDATE measurements SET location_id=NULL WHERE location_id IN (SELECT id FROM locations WHERE map_id=?)", (map_id,))
                con.execute("DELETE FROM locations WHERE map_id=?", (map_id,))
            else:
                con.execute("UPDATE locations SET map_id=NULL,x_percent=NULL,y_percent=NULL WHERE map_id=?", (map_id,))
            cur = con.execute("DELETE FROM maps WHERE id=?", (map_id,))
        try:
            (self.maps_dir / str(item["filename"])).unlink(missing_ok=True)
        except OSError:
            pass
        self.audit("map_delete", f"map:{map_id}", {"delete_locations": delete_locations}, user_name)
        return int(cur.rowcount)

    def save_location(self, payload: dict[str, object]) -> dict[str, object]:
        now = iso(utc_now())
        location_id = payload.get("id")
        values = (
            str(payload.get("name") or "Measurement site").strip(),
            str(payload.get("building") or "").strip(),
            str(payload.get("floor") or "").strip(),
            str(payload.get("room_type") or "").strip(),
            int(payload["map_id"]) if payload.get("map_id") not in (None, "") else None,
            max(0.0, min(100.0, float(payload["x_percent"]))) if payload.get("x_percent") not in (None, "") else None,
            max(0.0, min(100.0, float(payload["y_percent"]))) if payload.get("y_percent") not in (None, "") else None,
            float(payload["measurement_height_m"]) if payload.get("measurement_height_m") not in (None, "") else None,
            str(payload.get("notes") or "").strip(),
            1 if payload.get("active", True) else 0,
        )
        with self._connection() as con:
            if location_id:
                con.execute(
                    """
                    UPDATE locations SET name=?,building=?,floor=?,room_type=?,map_id=?,x_percent=?,y_percent=?,
                        measurement_height_m=?,notes=?,active=?,updated_at=? WHERE id=?
                    """,
                    (*values, now, int(location_id)),
                )
                saved_id = int(location_id)
            else:
                cur = con.execute(
                    """
                    INSERT INTO locations(name,building,floor,room_type,map_id,x_percent,y_percent,
                        measurement_height_m,notes,active,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (*values, now, now),
                )
                saved_id = int(cur.lastrowid)
        self.audit("location_save", f"location:{saved_id}", payload)
        return self.location(saved_id) or {}

    def location(self, location_id: int) -> dict[str, object] | None:
        with self._connection() as con:
            row = con.execute(
                """
                SELECT l.*, mp.filename AS map_filename, mp.name AS map_name,
                       COUNT(m.id) AS sample_count, MIN(m.completed_at) AS first_measurement,
                       MAX(m.completed_at) AS last_measurement, AVG(m.bq_m3) AS mean_bq_m3
                FROM locations l LEFT JOIN maps mp ON mp.id=l.map_id
                LEFT JOIN measurements m ON m.location_id=l.id
                WHERE l.id=? GROUP BY l.id
                """,
                (int(location_id),),
            ).fetchone()
        return dict(row) if row else None

    def locations(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                """
                SELECT l.*, mp.filename AS map_filename, mp.name AS map_name,
                       COUNT(m.id) AS sample_count, MIN(m.completed_at) AS first_measurement,
                       MAX(m.completed_at) AS last_measurement, AVG(m.bq_m3) AS mean_bq_m3,
                       (SELECT m2.bq_m3 FROM measurements m2 WHERE m2.location_id=l.id ORDER BY m2.completed_at DESC LIMIT 1) AS latest_bq_m3,
                       (SELECT m2.completed_at FROM measurements m2 WHERE m2.location_id=l.id ORDER BY m2.completed_at DESC LIMIT 1) AS latest_at
                FROM locations l LEFT JOIN maps mp ON mp.id=l.map_id
                LEFT JOIN measurements m ON m.location_id=l.id
                GROUP BY l.id ORDER BY l.active DESC,l.building,l.floor,l.name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_location(self, location_id: int, *, user_name: str | None = None) -> int:
        with self._connection() as con:
            con.execute("UPDATE measurements SET location_id=NULL, session_id=NULL WHERE location_id=?", (location_id,))
            con.execute("UPDATE sessions SET location_id=NULL WHERE location_id=?", (location_id,))
            con.execute("UPDATE events SET location_id=NULL WHERE location_id=?", (location_id,))
            cur = con.execute("DELETE FROM locations WHERE id=?", (location_id,))
        self.audit("location_delete", f"location:{location_id}", {}, user_name)
        return int(cur.rowcount)

    def assign_location(
        self,
        *,
        location_id: int,
        start: str,
        end: str | None,
        title: str,
        purpose: str = "",
        responsible: str = "",
        notes: str = "",
        device_id: str | None = None,
        user_name: str | None = None,
    ) -> dict[str, object]:
        start_dt = parse_dt(start)
        end_dt = parse_dt(end) if end else None
        if start_dt is None:
            raise StorageError("A valid session start is required")
        if end_dt and end_dt < start_dt:
            raise StorageError("Session end must be after start")
        with self._connection() as con:
            if con.execute("SELECT 1 FROM locations WHERE id=?", (int(location_id),)).fetchone() is None:
                raise StorageError("The selected measurement site does not exist")
            if device_id is None:
                device = con.execute("SELECT device_id FROM devices ORDER BY last_seen DESC LIMIT 1").fetchone()
                device_id = str(device["device_id"]) if device else None
            if device_id is None or con.execute("SELECT 1 FROM devices WHERE device_id=?", (device_id,)).fetchone() is None:
                raise StorageError("The selected measurement device does not exist")
            campaign = con.execute(
                "SELECT id FROM campaigns WHERE (? IS NULL OR device_id=?) ORDER BY active DESC,id DESC LIMIT 1",
                (device_id, device_id),
            ).fetchone()
            campaign_id = int(campaign["id"]) if campaign else None
            cur = con.execute(
                """
                INSERT INTO sessions(device_id,campaign_id,location_id,title,purpose,responsible,started_at,ended_at,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    device_id,
                    campaign_id,
                    int(location_id),
                    title.strip() or "Measurement session",
                    purpose.strip(),
                    responsible.strip(),
                    analysis_iso(start_dt),
                    analysis_iso(end_dt),
                    notes.strip(),
                    iso(utc_now()),
                ),
            )
            session_id = int(cur.lastrowid)
            clauses = ["completed_at>=?"]
            params: list[object] = [analysis_iso(start_dt)]
            if end_dt:
                clauses.append("completed_at<=?")
                params.append(analysis_iso(end_dt))
            if device_id:
                clauses.append("device_id=?")
                params.append(device_id)
            update = con.execute(
                f"UPDATE measurements SET location_id=?, session_id=? WHERE {' AND '.join(clauses)}",
                [int(location_id), session_id, *params],
            )
            assigned = int(update.rowcount)
        payload = {"session_id": session_id, "assigned": assigned, "location_id": location_id}
        self.audit("session_assign", f"session:{session_id}", payload, user_name)
        return payload

    def sessions(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                """
                SELECT s.*,l.name AS location_name,COUNT(m.id) AS sample_count,
                       MIN(m.completed_at) AS first_measurement,MAX(m.completed_at) AS last_measurement
                FROM sessions s LEFT JOIN locations l ON l.id=s.location_id
                LEFT JOIN measurements m ON m.session_id=s.id
                GROUP BY s.id ORDER BY s.started_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    # Events -------------------------------------------------------------
    def add_event(self, payload: dict[str, object], user_name: str | None = None) -> dict[str, object]:
        occurred = parse_dt(payload.get("occurred_at")) or utc_now()
        with self._connection() as con:
            cur = con.execute(
                "INSERT INTO events(session_id,location_id,event_type,occurred_at,title,notes,created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    int(payload["session_id"]) if payload.get("session_id") not in (None, "") else None,
                    int(payload["location_id"]) if payload.get("location_id") not in (None, "") else None,
                    str(payload.get("event_type") or "note"),
                    analysis_iso(occurred),
                    str(payload.get("title") or "Event").strip(),
                    str(payload.get("notes") or "").strip(),
                    iso(utc_now()),
                ),
            )
            event_id = int(cur.lastrowid)
        self.audit("event_add", f"event:{event_id}", payload, user_name)
        return self.event(event_id) or {}

    def event(self, event_id: int) -> dict[str, object] | None:
        with self._connection() as con:
            row = con.execute(
                "SELECT e.*,l.name AS location_name,s.title AS session_title FROM events e "
                "LEFT JOIN locations l ON l.id=e.location_id LEFT JOIN sessions s ON s.id=e.session_id WHERE e.id=?",
                (event_id,),
            ).fetchone()
        return dict(row) if row else None

    def events(self, *, start: str | None = None, end: str | None = None, location_id: int | None = None) -> list[dict[str, object]]:
        clauses: list[str] = []
        params: list[object] = []
        if start:
            clauses.append("e.occurred_at>=?")
            params.append(start)
        if end:
            clauses.append("e.occurred_at<=?")
            params.append(end)
        if location_id is not None:
            clauses.append("e.location_id=?")
            params.append(location_id)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connection() as con:
            rows = con.execute(
                "SELECT e.*,l.name AS location_name,s.title AS session_title FROM events e "
                "LEFT JOIN locations l ON l.id=e.location_id LEFT JOIN sessions s ON s.id=e.session_id" +
                where + " ORDER BY e.occurred_at DESC",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_event(self, event_id: int, user_name: str | None = None) -> int:
        with self._connection() as con:
            cur = con.execute("DELETE FROM events WHERE id=?", (event_id,))
        self.audit("event_delete", f"event:{event_id}", {}, user_name)
        return int(cur.rowcount)

    # Reports ------------------------------------------------------------
    def add_calibration(self, payload: dict[str, object], user_name: str | None = None) -> dict[str, object]:
        now=analysis_iso(utc_now())
        with self._connection() as con:
            cur=con.execute("INSERT INTO calibrations(device_id,calibrated_at,laboratory,certificate_reference,factor,relative_uncertainty_percent,next_due_at,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(payload.get("device_id"),payload.get("calibrated_at") or now,payload.get("laboratory"),payload.get("certificate_reference"),payload.get("factor"),payload.get("relative_uncertainty_percent"),payload.get("next_due_at"),payload.get("notes"),now))
            item=dict(con.execute("SELECT * FROM calibrations WHERE id=?",(cur.lastrowid,)).fetchone())
        self.audit("calibration_create",f"calibration:{item['id']}",item,user_name)
        return item

    def calibrations(self, device_id: str | None = None) -> list[dict[str, object]]:
        with self._connection() as con:
            if device_id:
                rows=con.execute("SELECT * FROM calibrations WHERE device_id=? ORDER BY calibrated_at DESC",(device_id,)).fetchall()
            else:
                rows=con.execute("SELECT * FROM calibrations ORDER BY calibrated_at DESC").fetchall()
        return [dict(r) for r in rows]

    def save_campaign_protocol(self, payload: dict[str, object], user_name: str | None = None) -> dict[str, object]:
        now=analysis_iso(utc_now()); campaign_id=int(payload["campaign_id"])
        fields=(payload.get("research_question"),payload.get("room_description"),payload.get("placement_description"),payload.get("distance_floor_m"),payload.get("distance_wall_m"),payload.get("ventilation_conditions"),payload.get("planned_end_at"),payload.get("responsible"),payload.get("notes"))
        with self._connection() as con:
            con.execute("INSERT INTO campaign_protocols(campaign_id,research_question,room_description,placement_description,distance_floor_m,distance_wall_m,ventilation_conditions,planned_end_at,responsible,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(campaign_id) DO UPDATE SET research_question=excluded.research_question,room_description=excluded.room_description,placement_description=excluded.placement_description,distance_floor_m=excluded.distance_floor_m,distance_wall_m=excluded.distance_wall_m,ventilation_conditions=excluded.ventilation_conditions,planned_end_at=excluded.planned_end_at,responsible=excluded.responsible,notes=excluded.notes,updated_at=excluded.updated_at",(campaign_id,*fields,now,now))
            item=dict(con.execute("SELECT * FROM campaign_protocols WHERE campaign_id=?",(campaign_id,)).fetchone())
        self.audit("campaign_protocol_save",f"campaign:{campaign_id}",item,user_name)
        return item

    def campaign_protocols(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows=con.execute("SELECT p.*,c.device_id,c.started_at AS campaign_started_at FROM campaign_protocols p JOIN campaigns c ON c.id=p.campaign_id ORDER BY c.started_at DESC").fetchall()
        return [dict(r) for r in rows]

    def add_report(self, metadata: dict[str, object]) -> dict[str, object]:
        with self._connection() as con:
            con.execute(
                """
                INSERT INTO reports(report_id,profile,locale,title,period_start,period_end,location_id,filename,sha256,created_at,metadata_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    metadata["report_id"], metadata["profile"], metadata["locale"], metadata["title"],
                    metadata.get("period_start"), metadata.get("period_end"), metadata.get("location_id"),
                    metadata["filename"], metadata["sha256"], metadata["created_at"],
                    json.dumps(metadata, ensure_ascii=False, default=str),
                ),
            )
        self.audit("report_create", f"report:{metadata['report_id']}", metadata)
        return metadata

    def reports(self) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT r.*,l.name AS location_name FROM reports r LEFT JOIN locations l ON l.id=r.location_id "
                "ORDER BY r.created_at DESC"
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                metadata = json.loads(str(item.pop("metadata_json")))
                item["metadata"] = metadata
                for key, value in metadata.items():
                    item.setdefault(key, value)
            except Exception:
                item["metadata"] = {}
            result.append(item)
        return result

    def report(self, report_id: str) -> dict[str, object] | None:
        with self._connection() as con:
            row = con.execute("SELECT * FROM reports WHERE report_id=?", (report_id,)).fetchone()
        return dict(row) if row else None

    def delete_report(self, report_id: str, user_name: str | None = None) -> int:
        item = self.report(report_id)
        if not item:
            return 0
        with self._connection() as con:
            cur = con.execute("DELETE FROM reports WHERE report_id=?", (report_id,))
        try:
            (self.reports_dir / str(item["filename"])).unlink(missing_ok=True)
        except OSError:
            pass
        self.audit("report_delete", f"report:{report_id}", {}, user_name)
        return int(cur.rowcount)

    # Audit and data management -----------------------------------------
    def audit(self, action: str, target: str | None, details: object, user_name: str | None = None) -> None:
        try:
            payload = json.dumps(details, ensure_ascii=False, default=str, separators=(",", ":"))
            with self._connection() as con:
                con.execute(
                    "INSERT INTO audit_log(action,target,details_json,created_at,user_name) VALUES(?,?,?,?,?)",
                    (action, target, payload, iso(utc_now()), user_name),
                )
        except Exception:
            # Auditing must never break the primary operation.
            pass

    def audit_entries(self, limit: int = 200) -> list[dict[str, object]]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (max(1, min(1000, int(limit))),)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["details"] = json.loads(str(item.pop("details_json")))
            except Exception:
                item["details"] = {}
            result.append(item)
        return result

    def data_summary(self) -> dict[str, object]:
        with self._connection() as con:
            counts = {
                table: int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("measurements", "devices", "campaigns", "maps", "locations", "sessions", "events", "reports")
            }
            range_row = con.execute(
                "SELECT MIN(completed_at) AS first_at,MAX(completed_at) AS last_at FROM measurements"
            ).fetchone()
            integrity = str(con.execute("PRAGMA integrity_check").fetchone()[0])
        file_size = self.path.stat().st_size if self.path.exists() else 0
        wal = Path(str(self.path) + "-wal")
        shm = Path(str(self.path) + "-shm")
        map_size = sum(p.stat().st_size for p in self.maps_dir.glob("*") if p.is_file())
        report_size = sum(p.stat().st_size for p in self.reports_dir.glob("*") if p.is_file())
        return {
            **counts,
            "database_path": str(self.path),
            "database_size_bytes": file_size + (wal.stat().st_size if wal.exists() else 0) + (shm.stat().st_size if shm.exists() else 0),
            "map_size_bytes": map_size,
            "report_size_bytes": report_size,
            "first_measurement": range_row["first_at"] if range_row else None,
            "last_measurement": range_row["last_at"] if range_row else None,
            "schema_version": SCHEMA_VERSION,
            "integrity": integrity,
        }

    def preview_delete(self, action: str, payload: dict[str, object]) -> dict[str, object]:
        with self._connection() as con:
            if action == "measurement_range":
                clauses = []
                params: list[object] = []
                if payload.get("start"):
                    clauses.append("completed_at>=?")
                    params.append(str(payload["start"]))
                if payload.get("end"):
                    clauses.append("completed_at<=?")
                    params.append(str(payload["end"]))
                if payload.get("device_id"):
                    clauses.append("device_id=?")
                    params.append(str(payload["device_id"]))
                if payload.get("location_id"):
                    clauses.append("location_id=?")
                    params.append(int(payload["location_id"]))
                where = " AND ".join(clauses) or "1=0"
                row = con.execute(
                    f"SELECT COUNT(*) AS n,MIN(completed_at) AS first_at,MAX(completed_at) AS last_at FROM measurements WHERE {where}",
                    params,
                ).fetchone()
                return {"action": action, "count": int(row["n"]), "first_at": row["first_at"], "last_at": row["last_at"]}
            if action == "device_history":
                device_id = str(payload.get("device_id") or "").strip()
                if not device_id:
                    return {"action": action, "count": 0, "device_id": None}
                row = con.execute(
                    "SELECT COUNT(*) AS n,MIN(completed_at) AS first_at,MAX(completed_at) AS last_at "
                    "FROM measurements WHERE device_id=?",
                    (device_id,),
                ).fetchone()
                return {"action": action, "count": int(row["n"]), "device_id": device_id, "first_at": row["first_at"], "last_at": row["last_at"]}
            if action == "campaign":
                campaign_id = int(payload.get("campaign_id") or 0)
                row = con.execute("SELECT COUNT(*) AS n FROM measurements WHERE campaign_id=?", (campaign_id,)).fetchone()
                return {"action": action, "count": int(row["n"]), "campaign_id": campaign_id}
            if action == "all_measurements":
                row = con.execute("SELECT COUNT(*) AS n,MIN(completed_at) AS first_at,MAX(completed_at) AS last_at FROM measurements").fetchone()
                return {"action": action, "count": int(row["n"]), "first_at": row["first_at"], "last_at": row["last_at"]}
            if action in {"all_reports", "all_events", "all_audit"}:
                table = {"all_reports": "reports", "all_events": "events", "all_audit": "audit_log"}[action]
                return {"action": action, "count": int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])}
            if action == "reset_database":
                return {"action": action, **self.data_summary()}
        raise StorageError("Unsupported delete action")

    def delete_data(self, action: str, payload: dict[str, object], user_name: str | None = None) -> dict[str, object]:
        preview = self.preview_delete(action, payload)
        backup_name = self.create_backup_file(prefix="pre-delete")
        deleted = 0
        report_files: list[str] = []
        with self._connection() as con:
            if action == "measurement_range":
                clauses = []
                params: list[object] = []
                if payload.get("start"):
                    clauses.append("completed_at>=?")
                    params.append(str(payload["start"]))
                if payload.get("end"):
                    clauses.append("completed_at<=?")
                    params.append(str(payload["end"]))
                if payload.get("device_id"):
                    clauses.append("device_id=?")
                    params.append(str(payload["device_id"]))
                if payload.get("location_id"):
                    clauses.append("location_id=?")
                    params.append(int(payload["location_id"]))
                if not clauses:
                    raise StorageError("A range or location is required")
                cur = con.execute(f"DELETE FROM measurements WHERE {' AND '.join(clauses)}", params)
                deleted = int(cur.rowcount)
            elif action == "device_history":
                device_id = str(payload.get("device_id") or "").strip()
                if not device_id:
                    raise StorageError("A device is required")
                deleted = int(con.execute("DELETE FROM measurements WHERE device_id=?", (device_id,)).rowcount)
                con.execute("DELETE FROM campaigns WHERE device_id=?", (device_id,))
                con.execute("DELETE FROM sessions WHERE device_id=?", (device_id,))
            elif action == "campaign":
                campaign_id = int(payload.get("campaign_id") or 0)
                cur = con.execute("DELETE FROM measurements WHERE campaign_id=?", (campaign_id,))
                deleted = int(cur.rowcount)
                con.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
            elif action == "all_measurements":
                deleted = int(con.execute("DELETE FROM measurements").rowcount)
                con.execute("DELETE FROM campaigns")
            elif action == "all_events":
                deleted = int(con.execute("DELETE FROM events").rowcount)
            elif action == "all_audit":
                deleted = int(con.execute("DELETE FROM audit_log").rowcount)
            elif action == "all_reports":
                report_files = [str(row[0]) for row in con.execute("SELECT filename FROM reports")]
                deleted = int(con.execute("DELETE FROM reports").rowcount)
            elif action == "reset_database":
                report_files = [str(row[0]) for row in con.execute("SELECT filename FROM reports")]
                deleted = int(con.execute("SELECT COUNT(*) FROM measurements").fetchone()[0])
                for table in ("measurements", "events", "sessions", "locations", "maps", "reports", "campaigns", "devices", "runtime"):
                    con.execute(f"DELETE FROM {table}")
            else:
                raise StorageError("Unsupported delete action")
        for filename in report_files:
            (self.reports_dir / filename).unlink(missing_ok=True)
        if action == "reset_database":
            for path in self.maps_dir.glob("*"):
                if path.is_file():
                    path.unlink(missing_ok=True)
        details = {"preview": preview, "deleted": deleted, "backup": backup_name}
        self.audit("data_delete", action, details, user_name)
        return details

    def _sqlite_backup_to(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            source = sqlite3.connect(self.path, timeout=20)
            target = sqlite3.connect(destination)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()

    def create_backup_file(self, prefix: str = "radon-monitoring") -> str:
        stamp = utc_now().strftime("%Y%m%d-%H%M%S")
        name = f"{prefix}-{stamp}.sqlite3"
        destination = self.backups_dir / name
        self._sqlite_backup_to(destination)
        return name

    def backup_zip_bytes(self) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            database = tmp_path / "radon-monitoring.sqlite3"
            self._sqlite_backup_to(database)
            manifest = {
                "app": "Radon Monitoring",
                "schema_version": SCHEMA_VERSION,
                "created_at": iso(utc_now()),
                "summary": self.data_summary(),
            }
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(database, "database/radon-monitoring.sqlite3")
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                for directory, prefix in ((self.maps_dir, "maps"), (self.reports_dir, "reports")):
                    for path in directory.glob("*"):
                        if path.is_file():
                            archive.write(path, f"{prefix}/{path.name}")
            return output.getvalue()

    @staticmethod
    def _validate_database(path: Path) -> None:
        con = sqlite3.connect(path)
        try:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise StorageError(f"Database integrity check failed: {integrity}")
            tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {"metadata", "devices", "campaigns", "measurements", "runtime"}
            if not required.issubset(tables):
                raise StorageError("Uploaded database is not a Radon Monitoring database")
        finally:
            con.close()

    def restore_database(self, data: bytes, filename: str, user_name: str | None = None) -> dict[str, object]:
        if len(data) > 250 * 1024 * 1024:
            raise StorageError("Backup is too large")
        backup_name = self.create_backup_file(prefix="pre-restore")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate = tmp_path / "candidate.sqlite3"
            if filename.lower().endswith(".zip") or data[:4] == b"PK\x03\x04":
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    members = archive.infolist()
                    total_uncompressed = sum(max(0, int(member.file_size)) for member in members)
                    if total_uncompressed > 300 * 1024 * 1024 or any(member.file_size > 250 * 1024 * 1024 for member in members):
                        raise StorageError("The expanded backup is too large")
                    names = [member.filename for member in members if member.filename.lower().endswith((".sqlite3", ".db"))]
                    if not names:
                        raise StorageError("The backup does not contain a database")
                    preferred = "database/radon-monitoring.sqlite3"
                    database_name = preferred if preferred in names else names[0]
                    candidate.write_bytes(archive.read(database_name))
                    extracted_maps: list[tuple[str, bytes]] = []
                    extracted_reports: list[tuple[str, bytes]] = []
                    for member in members:
                        name = member.filename
                        safe_name = Path(name).name
                        if not safe_name or member.is_dir():
                            continue
                        suffix = Path(safe_name).suffix.lower()
                        if name.startswith("maps/") and suffix in {".png", ".jpg", ".jpeg", ".webp"}:
                            extracted_maps.append((safe_name, archive.read(member)))
                        elif name.startswith("reports/") and suffix == ".pdf":
                            extracted_reports.append((safe_name, archive.read(member)))
            else:
                candidate.write_bytes(data)
                extracted_maps = []
                extracted_reports = []
            self._validate_database(candidate)
            with self._lock:
                for suffix in ("-wal", "-shm"):
                    Path(str(self.path) + suffix).unlink(missing_ok=True)
                os.replace(candidate, self.path)
                for directory in (self.maps_dir, self.reports_dir):
                    for existing in directory.glob("*"):
                        if existing.is_file():
                            existing.unlink(missing_ok=True)
                for name, content in extracted_maps:
                    (self.maps_dir / name).write_bytes(content)
                for name, content in extracted_reports:
                    (self.reports_dir / name).write_bytes(content)
            self._init_schema()
        result = {"restored": True, "pre_restore_backup": backup_name, "summary": self.data_summary()}
        self.audit("database_restore", "database", result, user_name)
        return result
