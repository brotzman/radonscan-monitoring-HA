import unittest
from datetime import datetime, timedelta, timezone

from radonscan3.analysis import analyse_records


class AnalysisTests(unittest.TestCase):
    def test_local_timezone_profiles(self):
        rows = [
            {"completed_at": "2026-01-15T06:00:00+00:00", "bq_m3": 100},
            {"completed_at": "2026-01-15T07:00:00+00:00", "bq_m3": 120},
        ]
        result = analyse_records(rows, timezone_name="Europe/Berlin")
        self.assertEqual(result["statistics"]["analysis_timezone"], "Europe/Berlin")
        self.assertEqual(result["hourly_profile"][7]["samples"], 1)
        self.assertEqual(result["hourly_profile"][8]["samples"], 1)

    def test_robust_statistics(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        values = [10, 11, 12, 13, 100]
        rows = [{"completed_at": (start + timedelta(hours=i)).isoformat(), "bq_m3": v} for i, v in enumerate(values)]
        stats = analyse_records(rows)["statistics"]
        self.assertEqual(stats["median_bq_m3"], 12)
        self.assertIsNotNone(stats["median_absolute_deviation_bq_m3"])
        self.assertIsNotNone(stats["theil_sen_slope_bq_m3_per_day"])

    def test_invalid_timezone_falls_back_to_utc(self):
        result = analyse_records([{"completed_at": "2026-01-01T00:00:00Z", "bq_m3": 50}], timezone_name="Invalid/Zone")
        self.assertEqual(result["statistics"]["analysis_timezone"], "UTC")


if __name__ == "__main__":
    unittest.main()
