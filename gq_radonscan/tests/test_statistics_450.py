from datetime import datetime, timedelta, timezone
from radonscan3.analysis import analyse_records

def rows(n=240):
    start=datetime(2026,1,1,tzinfo=timezone.utc)
    return [{"completed_at":(start+timedelta(hours=i)).isoformat(),"bq_m3":50+(i%24)*2,"raw_cph":30,"factor":1.54,"source":"device"} for i in range(n)]

def test_extended_statistics_are_available():
    result=analyse_records(rows())
    assert result["effective_sample_size"]["available"]
    assert result["confidence_intervals"]["mean"]["available"]
    assert result["mann_kendall"]["available"]
    assert "warning" in result["threshold_events"]
    assert len(result["concentration_classes"])==4

def test_short_series_does_not_invent_confidence_interval():
    result=analyse_records(rows(12))
    assert not result["confidence_intervals"]["mean"]["available"]
