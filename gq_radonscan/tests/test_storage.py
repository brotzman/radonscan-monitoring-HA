import sqlite3
import tempfile
import unittest
from pathlib import Path

from radonscan3.storage import Storage, SCHEMA_VERSION


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.tmp.name) / "radonscan.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_schema_and_factor_history(self):
        self.assertGreaterEqual(SCHEMA_VERSION, 7)
        self.assertTrue(self.storage.record_factor_configuration(1.53))
        self.assertFalse(self.storage.record_factor_configuration(1.53))
        self.assertTrue(self.storage.record_factor_configuration(1.60))
        self.assertEqual(len(self.storage.factor_history()), 2)

    def test_worldmap_queue_is_duplicate_safe(self):
        with self.storage._connection() as con:
            con.execute("INSERT INTO devices VALUES(?,?,?,?,?,?,?)", ("d1", "GQ", None, None, None, "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"))
            con.execute("INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)", ("d1", "2026-01-01T00:00:00+00:00", "test"))
            campaign_id = con.execute("SELECT id FROM campaigns").fetchone()[0]
            con.execute("INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)", ("d1", campaign_id, 1, "2099-01-01T00:00:00+00:00", 100, 153.0, 1.53, "test", "2099-01-01T00:00:00+00:00"))
        self.assertEqual(self.storage.queue_worldmap_measurements(max_age_hours=8760), 1)
        self.assertEqual(self.storage.queue_worldmap_measurements(max_age_hours=8760), 0)
        item = self.storage.next_worldmap_item()
        self.assertIsNotNone(item)
        self.storage.update_worldmap_item(item["id"], ok=False, error="network", retry_limit=2)
        self.assertEqual(self.storage.worldmap_queue_summary()["counts"].get("retry"), 1)
        # Make retry due immediately and fail terminally.
        with self.storage._connection() as con:
            con.execute("UPDATE worldmap_queue SET next_attempt_at=NULL")
        item = self.storage.next_worldmap_item()
        self.storage.update_worldmap_item(item["id"], ok=False, error="network", retry_limit=2)
        self.assertEqual(self.storage.worldmap_queue_summary()["counts"].get("failed"), 1)


if __name__ == "__main__":
    unittest.main()
