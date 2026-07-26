import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "rootfs/usr/local/lib/radonscan3/static"
LOCALES = ROOT / "rootfs/usr/local/lib/radonscan3/locales"
LOCALE_CODES = ("de", "en", "es", "fr", "hr", "it", "nl", "pl")
VISIBLE_VIEWS = ("overview", "analysis", "sites", "history", "reports", "data", "system", "settings", "help")


def _state(language="de"):
    return {
        "app": {"version": "5.3.2"},
        "settings": {
            "preferred_unit": "Bq/m3",
            "factor_bq_m3_per_cph": 1.54,
            "scan_interval": 300,
            "language": language,
            "warning_threshold_bq_m3": 100,
            "danger_threshold_bq_m3": 300,
            "minimum_data_coverage_percent": 95,
            "backfill_history": True,
            "history_retention_days": 1095,
            "serial_port": "auto",
            "data_management_enabled": True,
            "diagnostic_logging": False,
            "report_author": "A very long scientific author name used to test wrapping",
            "report_organisation": "Institute for Long Environmental Measurement Names",
            "analysis_timezone": "Europe/Berlin",
            "location_display_mode": "full",
            "gmcmap_enabled": False,
            "gmcmap_auto_upload": False,
            "gmcmap_upload_interval_minutes": 60,
            "gmcmap_account_id_masked": "12••••90",
            "gmcmap_device_id_masked": "AB••••YZ",
            "homeassistant_access_token_configured": False,
        },
        "connection": {"connected": True, "last_scan": "2026-07-25T16:00:00+00:00"},
        "device": {
            "device_id": "dev-1",
            "model": "GQ RadonScan",
            "firmware": "RadonScanRe2.02",
            "serial_number": "LONG-SERIAL-1234567890-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "serial_port": "/dev/serial/by-id/usb-GQ_Electronics_RadonScan_very_long_identifier",
        },
        "measurement": {
            "available": True,
            "device_id": "dev-1",
            "location_id": 1,
            "location_name": "Keller",
            "measurement_height_m": 1.1,
            "campaign_id": 7,
            "status": "normal",
            "bq_m3": 87.3,
            "pci_l": 2.36,
            "completed_at": "2026-07-25T16:00:00+00:00",
            "raw_cph": 57,
            "factor_bq_m3_per_cph": 1.54,
            "measurement_factor_bq_m3_per_cph": 1.53,
            "age_hours": 0.5,
        },
        "statistics": {
            "24h": {
                "available": True,
                "mean_bq_m3": 80,
                "coverage_percent": 100,
                "samples": 24,
                "required_samples": 24,
                "quality": "high",
                "observed_maximum_bq_m3": 112,
                "observed_maximum_at": "2026-07-25T15:00:00+00:00",
                "period_end": "2026-07-25T16:00:00+00:00",
            },
            "7d": {"available": False, "reason": "period_not_reached", "samples": 72, "required_samples": 168},
            "30d": {"available": False, "reason": "coverage_too_low", "coverage_percent": 84, "quality": "limited"},
            "all": {"available": True, "mean_bq_m3": 82, "minimum_bq_m3": 12, "maximum_bq_m3": 410, "quality": "good"},
        },
        "mqtt": {"connected": True},
        "homeassistant": {
            "connected": True,
            "location_name": "Home",
            "building_name": "Home",
            "address": "Linnenkamp 22, 44536 Lünen",
            "place_address": "Linnenkamp 22, 44536 Lünen",
            "latitude": 51.60176,
            "longitude": 7.45410,
            "elevation": 58,
            "country": "DE",
            "version": "2026.7",
            "time_zone": "Europe/Berlin",
        },
        "database": {
            "sample_count": 24,
            "total_sample_count": 500,
            "size_bytes": 1000000,
            "schema_version": 8,
            "integrity": "ok",
            "first_measurement": "2026-07-01T00:00:00+00:00",
            "last_measurement": "2026-07-25T16:00:00+00:00",
        },
        "protocol": {"transport": "GET/SPIR", "decoder": "radonscan3", "hourly_record_count": 500, "latest_raw_cph": 57, "latest_hour_index": 500, "block_sha256": {}},
        "catalog": {},
        "quality": {"label": "B"},
        "selection": {"explicit": True, "device_id": "dev-1", "location_id": 1, "campaign_id": 7},
    }


def _catalog():
    return {
        "devices": [{"device_id": "dev-1", "model": "GQ RadonScan", "serial_number": "RS-1"}],
        "locations": [{"id": 1, "name": "Keller", "room": "Keller", "building": "", "measurement_height_m": 1.1, "latest_bq_m3": 87.3, "latest_at": "2026-07-25T16:00:00+00:00", "sample_count": 24}],
        "homeassistant_location": {"connected": True, "location_name": "Home", "building_name": "Home", "address": "Linnenkamp 22, 44536 Lünen", "place_address": "Linnenkamp 22, 44536 Lünen"},
        "campaigns": [{"id": 7, "device_id": "dev-1", "active": 1, "started_at": "2026-07-24T16:00:00+00:00", "sample_count": 24}],
        "sessions": [{"id": 11, "device_id": "dev-1", "campaign_id": 7, "location_id": 1, "started_at": "2026-07-24T16:00:00+00:00"}],
        "events": [{"id": 1, "session_id": 11, "location_id": 1, "event_type": "ventilation", "occurred_at": "2026-07-25T15:00:00+00:00", "title": "Stoßlüftung", "notes": "Fenster vollständig geöffnet", "location_name": "Keller"}],
        "reports": [],
    }


def _history():
    return {
        "items": [
            {"device_id": "dev-1", "campaign_id": 7, "location_id": 1, "completed_at": "2026-07-25T14:00:00+00:00", "bq_m3": 75.0, "raw_cph": 49, "model": "GQ RadonScan", "serial_number": "RS-1", "location_name": "Keller"},
            {"device_id": "dev-1", "campaign_id": 7, "location_id": 1, "completed_at": "2026-07-25T15:00:00+00:00", "bq_m3": 112.0, "raw_cph": 73, "model": "GQ RadonScan", "serial_number": "RS-1", "location_name": "Keller"},
            {"device_id": "dev-1", "campaign_id": 7, "location_id": 1, "completed_at": "2026-07-25T16:00:00+00:00", "bq_m3": 87.3, "raw_cph": 57, "model": "GQ RadonScan", "serial_number": "RS-1", "location_name": "Keller"},
        ]
    }


def _fixture_html(locale="de") -> str:
    tr = json.loads((LOCALES / f"{locale}.json").read_text())
    locale_names = {code: code.upper() for code in LOCALE_CODES}
    html = (STATIC / "index.html").read_text()
    html = html.replace("__LOCALE__", locale).replace("__TRANSLATIONS__", json.dumps(tr)).replace("__LOCALE_NAMES__", json.dumps(locale_names)).replace("__VERSION__", "5.3.2").replace("__ACTION_TOKEN__", "test-token")
    html = html.replace('<link rel="stylesheet" href="assets/app.css?v=5.3.2">', "<style>" + (STATIC / "app.css").read_text() + "</style>")
    for script in ("core.js", "accessibility.js", "data-management.js", "app.js"):
        html = html.replace(f'<script src="assets/{script}?v=5.3.2"></script>', "<script>" + (STATIC / script).read_text() + "</script>")
    return html


def _payloads(language="de"):
    return {
        "api/state": _state(language),
        "api/catalog": _catalog(),
        "api/history": _history(),
        "api/gmcmap": {"status": {"enabled": False, "configured": False, "queue": {}}, "uploads": []},
        "api/audit": {"items": []},
        "api/data/reset": {"operation_id": "reset-test", "deleted_total_records": 501, "deleted_measurements": 500, "removed_files": 0, "backup": "automatic-test.sqlite3", "integrity": "ok", "database_size_before": 1000000, "database_size_after": 4096, "duration_ms": 42},
        "api/homeassistant/purge-all": {"operation_id": "purge-test", "detected_entities": 4, "submitted_globs": 5, "authentication": "long_lived_access_token", "keep_days": 0, "server_duration_ms": 55, "entity_ids": ["sensor.radonscan"], "entity_globs": ["sensor.radon*"]},
        "api/homeassistant/verify-purge": {"operation_id": "verify-test", "verified": True, "checked_entities": 4, "remaining_rows": 0, "checked_at": "2026-07-25T16:05:00+00:00", "period_start": "2026-06-25T16:05:00+00:00", "period_end": "2026-07-25T16:05:00+00:00", "limitation": "Recorder history API verification; long-term statistics may be retained separately."},
        "api/data/summary": {"measurements": 500, "first_measurement": "2026-07-01T00:00:00+00:00", "last_measurement": "2026-07-25T16:00:00+00:00", "database_size_bytes": 1000000, "integrity": "ok", "reports": 0, "report_size_bytes": 0, "schema_version": 8},
        "api/analysis": {"statistics": {}, "thresholds": {"warning": {}, "danger": {}}, "quality_control": {}, "uncertainty": {}, "scientific_quality": {}, "autocorrelation": {}, "change_point": {}, "records": [], "daily": [], "histogram": [], "weekday_profile": [], "hourly_profile": [], "weekly_heatmap": [], "events": []},
    }


def _launch_browser(p):
    return p.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox", "--allow-file-access-from-files"])


def _new_page(browser, width, height, locale="de", text_scale=1.0):
    html = _fixture_html(locale)
    page = browser.new_page(viewport={"width": width, "height": height})
    init_payloads = json.dumps(_payloads(locale))
    mock_script = f"""<script>window.__TEST_PAYLOADS__={init_payloads}; window.__TEST_CALLS__=[]; window.fetch = async (url, options={{}}) => {{ window.__TEST_CALLS__.push({{url:String(url),method:options.method||'GET',body:options.body||null,headers:options.headers||{{}}}}); const found=Object.entries(window.__TEST_PAYLOADS__).find(([k])=>String(url).includes(k)); const body=found?found[1]:{{}}; return new Response(JSON.stringify(body),{{status:200,headers:{{'Content-Type':'application/json'}}}}); }};</script>"""
    html = html.replace("<head>", "<head>" + mock_script, 1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.set_content(html, wait_until="load")
    if text_scale != 1.0:
        page.evaluate(f"document.documentElement.style.fontSize='{text_scale * 100}%'")
    page.wait_for_timeout(500)
    return page, errors



@pytest.fixture(scope="module")
def shared_browser():
    with sync_playwright() as p:
        browser = _launch_browser(p)
        yield browser
        browser.close()


def test_all_visible_views_have_no_horizontal_overflow(shared_browser):
    for width, height in ((320, 700), (390, 844), (768, 1024), (1440, 1000)):
        page, errors = _new_page(shared_browser, width, height)
        for view in VISIBLE_VIEWS:
            page.locator(f'[data-view="{view}"]').evaluate("(el)=>el.click()")
            page.wait_for_timeout(40)
            overflow = page.evaluate("""() => [...document.querySelectorAll('body *')].filter(e => {const s=getComputedStyle(e),r=e.getBoundingClientRect(); return !e.closest('#sidebar:not(.open), .table-wrap, .heatmap') && s.position!=='fixed' && r.width>0 && (r.right>document.documentElement.clientWidth+3 || r.left<-3)}).map(e=>({tag:e.tagName,id:e.id,cls:String(e.className),right:e.getBoundingClientRect().right})).slice(0,8)""")
            assert not overflow, f"{view} overflow at {width}px: {overflow}"
        assert not errors
        page.close()


def test_all_locales_render_without_missing_labels_or_mobile_overflow(shared_browser):
    for locale in LOCALE_CODES:
        page, errors = _new_page(shared_browser, 390, 844, locale)
        for view in VISIBLE_VIEWS:
            page.locator(f'[data-view="{view}"]').evaluate("(el)=>el.click()")
            page.wait_for_timeout(25)
        untranslated = page.evaluate("""() => [...document.querySelectorAll('[data-i18n]')].filter(el => !el.textContent.trim() || el.textContent.trim()===el.dataset.i18n).map(el=>el.dataset.i18n)""")
        overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 3")
        assert not untranslated, f"{locale}: untranslated {untranslated}"
        assert not overflow, f"{locale}: horizontal overflow"
        assert not errors, f"{locale}: {errors}"
        page.close()


def test_keyboard_navigation_accessible_names_and_large_text(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de", text_scale=2.0)
    page.keyboard.press("Tab")
    assert page.evaluate('document.activeElement.classList.contains("skip-link")')
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "mainContent"
    page.locator("#menuButton").focus()
    page.keyboard.press("Enter")
    assert page.locator("#sidebar").evaluate('(el)=>el.classList.contains("open")')
    page.keyboard.press("Escape")
    assert not page.locator("#sidebar").evaluate('(el)=>el.classList.contains("open")')

    for view in VISIBLE_VIEWS:
        page.locator(f'[data-view="{view}"]').evaluate("(el)=>el.click()")
        page.wait_for_timeout(25)
        unnamed = page.evaluate("""() => [...document.querySelectorAll('button:not([hidden]),a[href]:not([hidden]),input:not([type=hidden]),select,textarea')].filter(el => {const r=el.getBoundingClientRect(); if(r.width===0||r.height===0)return false; const label=el.getAttribute('aria-label')||el.textContent.trim()||el.getAttribute('title')||el.closest('label')?.innerText.trim(); return !label;}).map(el=>el.id||el.tagName)""")
        assert not unnamed, f"{view}: unnamed controls {unnamed}"
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 3")
    assert not errors
    page.close()


def test_destructive_workflows_submit_once_and_remain_inside_app(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    page.on("dialog", lambda dialog: dialog.accept())

    page.locator('[data-view="data"]').evaluate("(el)=>el.click()")
    page.locator("#deleteConfirmation").fill("LÖSCHEN")
    page.locator("#deleteDatabaseNow").click()
    page.wait_for_timeout(250)
    calls = page.evaluate("window.__TEST_CALLS__.filter(call => call.url.includes('api/data/reset'))")
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert page.evaluate("location.hash") == "#overview"

    page.locator('[data-view="data"]').evaluate("(el)=>el.click()")
    page.locator("#haConfirmation").fill("PURGE")
    page.locator("#purgeHaHistory").click()
    page.wait_for_timeout(250)
    calls = page.evaluate("window.__TEST_CALLS__.filter(call => call.url.includes('api/homeassistant/purge-all'))")
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert page.evaluate("location.hash") == "#overview"

    page.locator('[data-view="data"]').evaluate("(el)=>el.click()")
    page.locator("#verifyHaPurge").click()
    page.wait_for_timeout(200)
    calls = page.evaluate("window.__TEST_CALLS__.filter(call => call.url.includes('api/homeassistant/verify-purge'))")
    assert len(calls) == 1
    assert page.locator("#haOperationResult").get_attribute("hidden") is None
    assert "verify-test" in page.locator("#haOperationResult").inner_text()
    assert not errors
    page.close()


def test_overview_renders_home_assistant_location_with_coordinate_units(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    assert page.locator("#homeAssistantLocationTitle").inner_text() == "Home-Assistant-Standort"
    assert page.locator("#homeAssistantLocationAddress").inner_text() == "Linnenkamp 22, 44536 Lünen"
    assert page.locator("#homeAssistantLocationDetails").inner_text() == "Koordinaten: 51,60176° N, 7,45410° E · Höhe: 58 m · Land: DE · Zeitzone: Europe/Berlin"
    assert "Die Standortdaten stammen aus den allgemeinen Home-Assistant-Einstellungen und werden nicht an einen externen Geokodierungsdienst gesendet." in page.locator(".ha-location-privacy").inner_text()
    assert page.locator("#homeAssistantLocationPrivacyMode").inner_text() == "· Vollständig (Adresse und genaue Koordinaten)"
    assert not page.locator("#homeAssistantLocationCard").evaluate('(el)=>el.classList.contains("unavailable")')
    assert not errors
    page.close()


def test_location_privacy_modes_reduce_or_hide_precise_location(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    page.evaluate("window.__TEST_PAYLOADS__['api/state'].settings.location_display_mode='reduced'")
    page.locator("#refreshButton").click()
    page.wait_for_timeout(350)
    assert page.locator("#homeAssistantLocationAddress").inner_text() == "Home"
    assert page.locator("#homeAssistantLocationDetails").inner_text().startswith("Koordinaten: 51,60° N, 7,45° E")
    assert page.locator("#homeAssistantLocationPrivacyMode").inner_text() == "· Reduziert (Standortname und gerundete Koordinaten)"

    page.evaluate("window.__TEST_PAYLOADS__['api/state'].settings.location_display_mode='hidden'")
    page.locator("#refreshButton").click()
    page.wait_for_timeout(350)
    assert page.locator("#homeAssistantLocationCard").is_hidden()
    assert not errors
    page.close()


def test_overview_renders_radon_traffic_light_from_24_hour_mean(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    assert page.locator("#radonTrafficTitle").inner_text() == "Radonampel"
    assert page.locator("#radonTrafficStatus").inner_text() == "Unauffällig"
    assert page.locator("#radonTrafficValue").inner_text() == "24-Stunden-Mittelwert: 80,0 Bq/m³"
    assert page.locator("#radonTrafficBasis").inner_text() == "Bewertungsbasis: 24-Stunden-Mittelwert · Abdeckung: 100 %"
    assert page.locator("#radonTrafficThresholds").inner_text() == "Grün: < 100,0 · Gelb: 100,0–< 300,0 · Rot: ≥ 300,0 Bq/m³"
    assert page.locator(".radon-traffic-light.normal").evaluate('(el)=>el.classList.contains("active")')
    assert not page.locator(".radon-traffic-light.warning").evaluate('(el)=>el.classList.contains("active")')
    assert not page.locator(".radon-traffic-light.danger").evaluate('(el)=>el.classList.contains("active")')
    assert page.locator("#radonTrafficSignal").get_attribute("aria-label") == "Radonampel: Unauffällig"
    assert not errors
    page.close()


def test_radon_traffic_light_falls_back_to_provisional_hourly_value(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    page.evaluate("""() => {const p=window.__TEST_PAYLOADS__['api/state'].statistics['24h'];p.available=false;p.reason='period_not_reached';p.coverage_percent=54;}""")
    page.locator("#refreshButton").click()
    page.wait_for_timeout(350)
    assert page.locator("#radonTrafficValue").inner_text() == "Aktueller Wert: 87,3 Bq/m³"
    assert page.locator("#radonTrafficBasis").inner_text() == "Bewertungsbasis: letzter abgeschlossener Stundenwert · vorläufig · Abdeckung: 54 %"
    assert not errors
    page.close()


def test_overview_context_is_persistent_filter_and_peak_replaces_overall_average(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    assert page.locator("#overviewDevice").input_value() == "dev-1"
    assert page.locator("#overviewLocation").count() == 0
    assert page.locator("#homeAssistantRoom").inner_text() == "Raum: Keller · Messhöhe: 1,1 m"
    assert page.locator("#overviewCampaign").input_value() == "7"
    assert page.locator("#peak24").inner_text() == "112,0 Bq/m³"
    assert "25.07.2026" in page.locator("#peak24Time").inner_text()
    assert page.locator("#overviewDatabaseStatus").inner_text().startswith("24 / 500")

    page.evaluate("window.__TEST_CALLS__=[]")
    page.locator("#overviewApply").click()
    page.wait_for_timeout(250)
    calls = page.evaluate("window.__TEST_CALLS__.map(call=>call.url)")
    assert any("api/state?scope=selection" in url and "device_id=dev-1" in url and "location_id=1" not in url and "campaign_id=7" in url for url in calls)
    assert any("api/history?" in url and "device_id=dev-1" in url and "location_id=1" in url and "campaign_id=7" in url for url in calls)
    assert not errors
    page.close()


def test_sites_and_events_are_separate_from_optional_world_map_and_marked_in_chart(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    assert page.locator("#gmcmapNav").is_hidden()
    assert page.locator("#view-map").is_hidden()
    assert page.locator("#view-sites #locationForm").count() == 1
    assert page.locator("#view-sites #eventForm").count() == 1
    assert page.locator("#locationRoom").count() == 1
    assert page.locator("#locationName").count() == 0
    assert page.locator("#haRoomBuilding").inner_text() == "Home"
    assert page.locator("#haRoomPlace").inner_text() == "Linnenkamp 22, 44536 Lünen"
    assert page.locator("#view-map #locationForm").count() == 0
    assert page.locator("#chart .event-marker").count() == 1
    assert page.locator("#chart .event-marker-dot title").text_content().endswith("Stoßlüftung · Keller · Fenster vollständig geöffnet")
    page.locator('[data-view="sites"]').evaluate("el=>el.click()")
    assert page.locator("#view-sites").evaluate('(el)=>el.classList.contains("active")')
    assert not errors
    page.close()


def test_room_form_submits_only_room_and_measurement_height(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    page.locator('[data-view="sites"]').evaluate("el=>el.click()")
    page.evaluate("window.__TEST_CALLS__=[]")
    assert page.locator("#locationRoom").get_attribute("name") == "room"
    assert page.locator("#locationHeight").get_attribute("name") == "measurement_height_m"
    page.locator("#locationRoom").fill("   ")
    page.locator("#locationForm button[type=submit]").evaluate("el=>el.click()")
    page.wait_for_timeout(100)
    empty_calls = page.evaluate("window.__TEST_CALLS__.filter(call=>call.url.includes('api/locations') && call.method==='POST')")
    assert empty_calls == []
    assert "Raum" in page.locator("#toast").inner_text()
    page.locator("#locationRoom").fill("  Arbeitszimmer  ")
    page.locator("#locationHeight").fill("1.2")
    page.locator("#locationForm button[type=submit]").click()
    page.wait_for_timeout(250)
    calls = page.evaluate("window.__TEST_CALLS__.filter(call=>call.url.includes('api/locations') && call.method==='POST')")
    assert len(calls) == 1
    body = json.loads(calls[0]["body"])
    assert body == {"id": None, "room": "Arbeitszimmer", "name": "Arbeitszimmer", "measurement_height_m": 1.2}
    assert calls[0]["headers"]["X-Radon-Room"] == "Arbeitszimmer"
    assert calls[0]["headers"]["X-Radon-Measurement-Height"] == "1.2"
    assert not errors
    page.close()

def test_analysis_starts_with_summary_and_collapsed_scientific_details(shared_browser):
    page, errors = _new_page(shared_browser, 390, 844, "de")
    page.locator('[data-view="analysis"]').evaluate("el=>el.click()")
    page.wait_for_timeout(200)
    assert page.locator("#analysisSummaryText").inner_text()
    assert not page.locator("#analysisAdvanced").evaluate("el=>el.open")
    assert not errors
    page.close()
