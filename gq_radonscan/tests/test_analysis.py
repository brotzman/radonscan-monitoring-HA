import unittest
from datetime import datetime, timedelta, timezone

from radonscan3.analysis import analyse_event_impacts, analyse_records


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

    def test_rolling_and_percentile_statistics(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = [{"completed_at": (start + timedelta(hours=i)).isoformat(), "bq_m3": 50 + i} for i in range(30)]
        stats = analyse_records(rows)["statistics"]
        self.assertIsNotNone(stats["rolling_24h_mean_bq_m3"])
        self.assertIsNotNone(stats["rolling_24h_highest_mean_bq_m3"])
        self.assertGreaterEqual(stats["p99_bq_m3"], stats["p95_bq_m3"])
        self.assertEqual(stats["gap_count"], 0)

    def test_event_impacts_summary(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = []
        for i in range(48):
            value = 100 if i < 12 else 60 if i < 24 else 95
            rows.append({"completed_at": (start + timedelta(hours=i)).isoformat(), "bq_m3": value})
        events = [{"occurred_at": (start + timedelta(hours=12)).isoformat(), "event_type": "ventilation", "title": "Open window"}]
        impact = analyse_event_impacts(rows, events)
        self.assertTrue(impact["available"])
        self.assertEqual(impact["evaluated_events"], 1)
        self.assertGreater(impact["average_drop_bq_m3"], 0)


if __name__ == "__main__":
    unittest.main()
