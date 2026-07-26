from pathlib import Path


def test_purge_endpoint_calls_existing_radon_entity_method():
    web_source = (Path(__file__).resolve().parents[1] / "rootfs/usr/local/lib/radonscan3/web.py").read_text(encoding="utf-8")
    assert "radon_entities()" in web_source
    assert "app.ha.radonscan_entities()" not in web_source
