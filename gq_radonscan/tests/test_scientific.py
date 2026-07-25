from datetime import datetime,timedelta,timezone
from radonscan3.analysis import analyse_records

def rows(n=72):
    start=datetime(2026,1,1,tzinfo=timezone.utc)
    return [{"completed_at":(start+timedelta(hours=i)).isoformat(),"bq_m3":100+(i>=36)*50,"raw_cph":100+(i>=36)*50,"factor":1.0,"source":"device"} for i in range(n)]

def test_uncertainty_and_quality_class():
    result=analyse_records(rows(),start=datetime(2026,1,1,tzinfo=timezone.utc),end=datetime(2026,1,3,23,tzinfo=timezone.utc))
    assert result["uncertainty"]["available"] is True
    assert result["statistics"]["scientific_quality_class"] in {"A","B","C","D"}
    assert result["quality_control"]["status"] == "clean"

def test_change_point_is_candidate():
    result=analyse_records(rows())
    assert result["change_point"]["available"] is True
    assert result["change_point"]["interpretation"] == "candidate_only"
