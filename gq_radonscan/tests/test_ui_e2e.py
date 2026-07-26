import json
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "rootfs/usr/local/lib/radonscan3/static"
LOCALES = ROOT / "rootfs/usr/local/lib/radonscan3/locales"
LOCALE_CODES = ("de", "en", "es", "fr", "hr", "it", "nl", "pl")


def _state(language="de"):
    return {
        "app": {"version": "5.1.0"},
        "settings": {"preferred_unit":"Bq/m3","factor_bq_m3_per_cph":1.54,"scan_interval":300,"language":language,"warning_threshold_bq_m3":100,"danger_threshold_bq_m3":300,"minimum_data_coverage_percent":95,"backfill_history":True,"history_retention_days":1095,"serial_port":"auto","data_management_enabled":True,"diagnostic_logging":False,"report_author":"A very long scientific author name used to test wrapping","report_organisation":"Institute for Long Environmental Measurement Names","analysis_timezone":"Europe/Berlin","gmcmap_enabled":False,"gmcmap_auto_upload":False,"gmcmap_upload_interval_minutes":60,"gmcmap_account_id_masked":"12••••90","gmcmap_device_id_masked":"AB••••YZ","homeassistant_access_token_configured":False},
        "connection":{"connected":True,"last_scan":"2026-07-25T16:00:00+00:00"},
        "device":{"model":"GQ RadonScan","firmware":"RadonScanRe2.02","serial_number":"LONG-SERIAL-1234567890-ABCDEFGHIJKLMNOPQRSTUVWXYZ","serial_port":"/dev/serial/by-id/usb-GQ_Electronics_RadonScan_very_long_identifier"},
        "measurement":{"available":True,"bq_m3":87.3,"pci_l":2.36,"completed_at":"2026-07-25T16:00:00+00:00","raw_cph":57,"factor_bq_m3_per_cph":1.54,"measurement_factor_bq_m3_per_cph":1.53,"age_hours":0.5},
        "statistics":{"24h":{"available":True,"mean_bq_m3":80,"coverage_percent":100,"samples":24,"required_samples":24,"quality":"high"},"7d":{"available":False,"reason":"period_not_reached","samples":72,"required_samples":168},"30d":{"available":False,"reason":"coverage_too_low","coverage_percent":84,"quality":"limited"},"all":{"available":True,"mean_bq_m3":82,"minimum_bq_m3":12,"maximum_bq_m3":410,"quality":"good"}},
        "mqtt":{"connected":True},"homeassistant":{"connected":True,"location_name":"Home","address":"Linnenkamp 22, 44536 Lünen","latitude":51.60176,"longitude":7.45410,"elevation":58,"country":"DE","version":"2026.7","time_zone":"Europe/Berlin"},
        "database":{"sample_count":500,"size_bytes":1000000,"schema_version":8,"integrity":"ok","first_measurement":"2026-07-01T00:00:00+00:00","last_measurement":"2026-07-25T16:00:00+00:00"},
        "protocol":{"transport":"GET/SPIR","decoder":"radonscan3","hourly_record_count":500,"latest_raw_cph":57,"latest_hour_index":500,"block_sha256":{}},
        "catalog":{},"quality":{"label":"B"},
    }


def _fixture_html(locale="de") -> str:
    tr=json.loads((LOCALES/f'{locale}.json').read_text())
    locale_names={code: code.upper() for code in LOCALE_CODES}
    html=(STATIC/'index.html').read_text()
    html=html.replace('__LOCALE__',locale).replace('__TRANSLATIONS__',json.dumps(tr)).replace('__LOCALE_NAMES__',json.dumps(locale_names)).replace('__VERSION__','5.1.0').replace('__ACTION_TOKEN__','test-token')
    html=html.replace('<link rel="stylesheet" href="assets/app.css?v=5.1.0">', '<style>'+ (STATIC/'app.css').read_text() +'</style>')
    for script in ('core.js','accessibility.js','data-management.js','app.js'):
        html=html.replace(f'<script src="assets/{script}?v=5.1.0"></script>', '<script>'+ (STATIC/script).read_text() +'</script>')
    return html


def _payloads(language="de"):
    return {
        'api/state':_state(language), 'api/catalog':{"devices":[],"locations":[],"campaigns":[],"events":[],"reports":[]},
        'api/history':{"items":[]}, 'api/gmcmap':{"status":{"enabled":False,"configured":False,"queue":{}},"uploads":[]},
        'api/audit':{"items":[]},
        'api/data/reset':{"operation_id":"reset-test","deleted_total_records":501,"deleted_measurements":500,"removed_files":0,"backup":"automatic-test.sqlite3","integrity":"ok","database_size_before":1000000,"database_size_after":4096,"duration_ms":42},
        'api/homeassistant/purge-all':{"operation_id":"purge-test","detected_entities":4,"submitted_globs":5,"authentication":"long_lived_access_token","keep_days":0,"server_duration_ms":55,"entity_ids":["sensor.radonscan"],"entity_globs":["sensor.radon*"]},
        'api/homeassistant/verify-purge':{"operation_id":"verify-test","verified":True,"checked_entities":4,"remaining_rows":0,"checked_at":"2026-07-25T16:05:00+00:00","period_start":"2026-06-25T16:05:00+00:00","period_end":"2026-07-25T16:05:00+00:00","limitation":"Recorder history API verification; long-term statistics may be retained separately."},
        'api/data/summary':{"measurements":500,"first_measurement":"2026-07-01T00:00:00+00:00","last_measurement":"2026-07-25T16:00:00+00:00","database_size_bytes":1000000,"integrity":"ok","reports":0,"report_size_bytes":0,"schema_version":8},
        'api/analysis':{"statistics":{},"thresholds":{"warning":{},"danger":{}},"quality_control":{},"uncertainty":{},"scientific_quality":{},"autocorrelation":{},"change_point":{},"records":[],"daily":[],"histogram":[],"weekday_profile":[],"hourly_profile":[],"weekly_heatmap":[],"events":[]}
    }


def _open_page(p, width, height, locale="de", text_scale=1.0):
    html=_fixture_html(locale)
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--allow-file-access-from-files'])
    page=browser.new_page(viewport={"width":width,"height":height})
    init_payloads=json.dumps(_payloads(locale))
    mock_script=f"""<script>window.__TEST_PAYLOADS__={init_payloads}; window.__TEST_CALLS__=[]; window.fetch = async (url, options={{}}) => {{ window.__TEST_CALLS__.push({{url:String(url),method:options.method||'GET',body:options.body||null,headers:options.headers||{{}}}}); const found=Object.entries(window.__TEST_PAYLOADS__).find(([k])=>String(url).includes(k)); const body=found?found[1]:{{}}; return new Response(JSON.stringify(body),{{status:200,headers:{{'Content-Type':'application/json'}}}}); }};</script>"""
    html=html.replace('<head>', '<head>'+mock_script, 1)
    errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
    page.set_content(html,wait_until='load')
    if text_scale != 1.0:
        page.evaluate(f"document.documentElement.style.fontSize='{text_scale*100}%'")
    page.wait_for_timeout(350)
    return browser,page,errors


@pytest.mark.parametrize('width,height',[(320,700),(390,844),(768,1024),(1440,1000)])
def test_all_views_have_no_horizontal_overflow(width,height):
    with sync_playwright() as p:
        browser,page,errors=_open_page(p,width,height)
        for view in ['overview','analysis','map','history','reports','data','system','settings','help']:
            page.locator(f'[data-view="{view}"]').evaluate('(el)=>el.click()')
            page.wait_for_timeout(40)
            overflow=page.evaluate("""() => [...document.querySelectorAll('body *')].filter(e => {const s=getComputedStyle(e),r=e.getBoundingClientRect(); return !e.closest('#sidebar:not(.open), .table-wrap, .heatmap') && s.position!=='fixed' && r.width>0 && (r.right>document.documentElement.clientWidth+3 || r.left<-3)}).map(e=>({tag:e.tagName,id:e.id,cls:String(e.className),right:e.getBoundingClientRect().right})).slice(0,8)""")
            assert not overflow, f'{view} overflow at {width}px: {overflow}'
        assert not errors
        browser.close()


@pytest.mark.parametrize('locale',LOCALE_CODES)
def test_all_locales_render_without_missing_labels_or_mobile_overflow(locale):
    with sync_playwright() as p:
        browser,page,errors=_open_page(p,390,844,locale)
        for view in ['overview','analysis','map','history','reports','data','system','settings','help']:
            page.locator(f'[data-view="{view}"]').evaluate('(el)=>el.click()')
            page.wait_for_timeout(25)
        untranslated=page.evaluate("""() => [...document.querySelectorAll('[data-i18n]')].filter(el => !el.textContent.trim() || el.textContent.trim()===el.dataset.i18n).map(el=>el.dataset.i18n)""")
        overflow=page.evaluate("""() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 3""")
        assert not untranslated, f'{locale}: untranslated {untranslated}'
        assert not overflow, f'{locale}: horizontal overflow'
        assert not errors, f'{locale}: {errors}'
        browser.close()


def test_keyboard_navigation_accessible_names_and_large_text():
    with sync_playwright() as p:
        browser,page,errors=_open_page(p,390,844,'de',text_scale=2.0)
        # Skip link and menu must be operable by keyboard.
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement.classList.contains("skip-link")')
        page.keyboard.press('Enter')
        assert page.evaluate('document.activeElement.id') == 'mainContent'
        page.locator('#menuButton').focus(); page.keyboard.press('Enter')
        assert page.locator('#sidebar').evaluate('(el)=>el.classList.contains("open")')
        page.keyboard.press('Escape')
        assert not page.locator('#sidebar').evaluate('(el)=>el.classList.contains("open")')

        for view in ['overview','analysis','map','history','reports','data','system','settings','help']:
            page.locator(f'[data-view="{view}"]').evaluate('(el)=>el.click()')
            page.wait_for_timeout(25)
            unnamed=page.evaluate("""() => [...document.querySelectorAll('button:not([hidden]),a[href]:not([hidden]),input:not([type=hidden]),select,textarea')].filter(el => {const r=el.getBoundingClientRect(); if(r.width===0||r.height===0)return false; const label=el.getAttribute('aria-label')||el.textContent.trim()||el.getAttribute('title')||el.closest('label')?.innerText.trim(); return !label;}).map(el=>el.id||el.tagName)""")
            assert not unnamed, f'{view}: unnamed controls {unnamed}'
        assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth + 3')
        assert not errors
        browser.close()


def test_destructive_workflows_submit_once_and_remain_inside_app():
    with sync_playwright() as p:
        browser,page,errors=_open_page(p,390,844,'de')
        page.on('dialog', lambda dialog: dialog.accept())

        page.locator('[data-view="data"]').evaluate('(el)=>el.click()')
        page.locator('#deleteConfirmation').fill('LÖSCHEN')
        page.locator('#deleteDatabaseNow').click()
        page.wait_for_timeout(250)
        calls=page.evaluate("window.__TEST_CALLS__.filter(call => call.url.includes('api/data/reset'))")
        assert len(calls)==1
        assert calls[0]['method']=='POST'
        assert page.evaluate('location.hash')=='#overview'

        page.locator('[data-view="data"]').evaluate('(el)=>el.click()')
        page.locator('#haConfirmation').fill('PURGE')
        page.locator('#purgeHaHistory').click()
        page.wait_for_timeout(250)
        calls=page.evaluate("window.__TEST_CALLS__.filter(call => call.url.includes('api/homeassistant/purge-all'))")
        assert len(calls)==1
        assert calls[0]['method']=='POST'
        assert page.evaluate('location.hash')=='#overview'

        page.locator('[data-view="data"]').evaluate('(el)=>el.click()')
        page.locator('#verifyHaPurge').click()
        page.wait_for_timeout(200)
        calls=page.evaluate("window.__TEST_CALLS__.filter(call => call.url.includes('api/homeassistant/verify-purge'))")
        assert len(calls)==1
        assert page.locator('#haOperationResult').get_attribute('hidden') is None
        assert 'verify-test' in page.locator('#haOperationResult').inner_text()
        assert not errors
        browser.close()


def test_overview_renders_home_assistant_location_from_local_config():
    with sync_playwright() as p:
        browser,page,errors=_open_page(p,390,844,'de')
        assert page.locator('#homeAssistantLocationTitle').inner_text()=='Home-Assistant-Standort'
        assert page.locator('#homeAssistantLocationAddress').inner_text()=='Linnenkamp 22, 44536 Lünen'
        assert page.locator('#homeAssistantLocationDetails').inner_text()=='Koordinaten: 51,60176, 7,45410 · Höhe: 58 m · Land: DE · Zeitzone: Europe/Berlin'
        assert page.locator('.ha-location-privacy').inner_text()=='Die Standortdaten stammen aus den allgemeinen Home-Assistant-Einstellungen und werden nicht an einen externen Geokodierungsdienst gesendet.'
        assert not page.locator('#homeAssistantLocationCard').evaluate('(el)=>el.classList.contains("unavailable")')
        assert not errors
        browser.close()

def test_overview_renders_radon_traffic_light_from_configured_thresholds():
    with sync_playwright() as p:
        browser,page,errors=_open_page(p,390,844,'de')
        assert page.locator('#radonTrafficTitle').inner_text()=='Radonampel'
        assert page.locator('#radonTrafficStatus').inner_text()=='Unauffällig'
        assert page.locator('#radonTrafficValue').inner_text()=='Aktueller Wert: 87,3 Bq/m³'
        assert page.locator('#radonTrafficThresholds').inner_text()=='Grün: < 100,0 · Gelb: 100,0–< 300,0 · Rot: ≥ 300,0 Bq/m³'
        assert page.locator('.radon-traffic-light.normal').evaluate('(el)=>el.classList.contains("active")')
        assert not page.locator('.radon-traffic-light.warning').evaluate('(el)=>el.classList.contains("active")')
        assert not page.locator('.radon-traffic-light.danger').evaluate('(el)=>el.classList.contains("active")')
        assert page.locator('#radonTrafficSignal').get_attribute('aria-label')=='Radonampel: Unauffällig'
        assert not errors
        browser.close()

