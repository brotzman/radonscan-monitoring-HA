import tempfile
import time
import unittest
from pathlib import Path

from radonscan3.storage import Storage, StorageError


class PerformanceAndRestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.storage=Storage(Path(self.tmp.name)/'radonscan.sqlite3')
    def tearDown(self): self.tmp.cleanup()

    def test_corrupt_restore_is_rejected_without_replacing_database(self):
        before=self.storage.data_summary()
        with self.assertRaises((StorageError, Exception)):
            self.storage.restore_database(b'not a sqlite database','broken.sqlite3')
        after=self.storage.data_summary()
        self.assertEqual(before['schema_version'],after['schema_version'])
        self.assertEqual(after['integrity'],'ok')

    def test_three_year_summary_remains_fast(self):
        with self.storage._connection() as con:
            con.execute("INSERT INTO devices VALUES(?,?,?,?,?,?,?)",('d1','GQ',None,None,None,'2023-01-01T00:00:00+00:00','2026-01-01T00:00:00+00:00'))
            con.execute("INSERT INTO campaigns(device_id,started_at,reason,active) VALUES(?,?,?,1)",('d1','2023-01-01T00:00:00+00:00','test'))
            cid=con.execute('SELECT id FROM campaigns').fetchone()[0]
            rows=[]
            from datetime import datetime,timedelta,timezone
            start=datetime(2023,1,1,tzinfo=timezone.utc)
            for i in range(3*365*24):
                dt=(start+timedelta(hours=i)).isoformat()
                rows.append(('d1',cid,i,dt,50,76.5,1.53,'test',dt))
            con.executemany('INSERT INTO measurements(device_id,campaign_id,hour_index,completed_at,raw_cph,bq_m3,factor,source,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)',rows)
        t=time.perf_counter(); summary=self.storage.data_summary(); elapsed=time.perf_counter()-t
        self.assertEqual(summary['measurements'],3*365*24)
        self.assertLess(elapsed,2.0)

if __name__=='__main__': unittest.main()
