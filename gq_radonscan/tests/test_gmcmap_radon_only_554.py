from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch
import io
import urllib.error

from radonscan3.gmcmap import GmcMapClient, RADON_ENDPOINT


class FakeStorage:
    def __init__(self) -> None:
        self.runtime = {}
        self.recorded = []
        self.audited = []

    def latest(self):
        return {
            "completed_at": "2026-07-27T10:00:00+00:00",
            "bq_m3": 74.0,
        }

    def get_runtime(self, _key, default):
        return self.runtime or default

    def set_runtime(self, _key, value):
        self.runtime = value

    def worldmap_queue_summary(self):
        return {"pending_total": 0, "oldest_pending": None}

    def queue_worldmap_measurements(self, **_kwargs):
        return 0

    def next_worldmap_item(self):
        return None

    def update_worldmap_item(self, *_args, **_kwargs):
        raise AssertionError("Manual upload must not update a queue item")

    def record_worldmap_upload(self, result, user_name=None):
        self.recorded.append((result, user_name))

    def audit(self, action, target, result, user_name=None):
        self.audited.append((action, target, result, user_name))


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit):
        return b"OK"


def settings():
    return SimpleNamespace(
        gmcmap_enabled=True,
        gmcmap_auto_upload=False,
        gmcmap_account_id="account-123",
        gmcmap_device_id="radon-456",
        gmcmap_upload_interval_minutes=60,
        gmcmap_max_age_hours=72,
        gmcmap_retry_limit=8,
    )


def test_radon_upload_uses_public_endpoint_without_radioactivity_fields():
    storage = FakeStorage()
    client = GmcMapClient(settings(), storage)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["user_agent"] = request.headers.get("User-agent")
        return FakeResponse()

    with patch("radonscan3.gmcmap.urllib.request.urlopen", fake_urlopen):
        result = client.upload_latest()

    parsed = urlparse(captured["url"])
    fields = parse_qs(parsed.query)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == RADON_ENDPOINT
    assert fields == {
        "AID": ["account-123"],
        "GID": ["radon-456"],
        "pCi": ["2.0000"],
    }
    assert "CPM" not in fields
    assert "ACPM" not in fields
    assert "uSV" not in fields
    assert result["ok"] is True
    assert result["upload_mode"] == "radon_only"
    assert result["endpoint"] == RADON_ENDPOINT
    assert captured["user_agent"] == "Radon-Monitoring/5.5.10"


def test_status_explicitly_describes_radon_only_submission():
    status = GmcMapClient(settings(), FakeStorage()).status()
    assert status["endpoint"] == RADON_ENDPOINT
    assert status["upload_mode"] == "radon_only"
    assert status["submitted_fields"] == ["AID", "GID", "pCi"]


def test_http_error_records_status_and_response_body():
    storage = FakeStorage()
    client = GmcMapClient(settings(), storage)
    error = urllib.error.HTTPError(
        RADON_ENDPOINT,
        404,
        "Not Found",
        hdrs=None,
        fp=io.BytesIO(b"Not Found"),
    )
    with patch("radonscan3.gmcmap.urllib.request.urlopen", side_effect=error):
        try:
            client.upload_latest()
        except Exception as exc:
            assert "HTTP 404" in str(exc)
        else:
            raise AssertionError("Expected upload failure")
    assert storage.runtime["http_status"] == 404
    assert storage.runtime["response"] == "Not Found"
