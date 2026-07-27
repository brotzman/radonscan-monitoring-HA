import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'rootfs/usr/local/lib/radonscan3'
STATIC = LIB / 'static'
LOCALES = LIB / 'locales'


def test_release_versions_are_consistent():
    assert 'version: 5.5.0' in (ROOT / 'config.yaml').read_text(encoding='utf-8')
    assert 'BUILD_VERSION="5.5.0"' in (ROOT / 'Dockerfile').read_text(encoding='utf-8')
    assert '__version__ = "5.5.0"' in (LIB / '__init__.py').read_text(encoding='utf-8')
    assert 'Radon Monitoring 5.5.0' in (ROOT / 'README.md').read_text(encoding='utf-8')


def test_current_manuals_exist_and_obsolete_manuals_are_removed():
    docs = ROOT / 'rootfs/usr/local/share/radonscan3/docs'
    for lang in ('de', 'en'):
        path = docs / f'Radon_Monitoring_User_Manual_5.5.0_{lang}.pdf'
        assert path.is_file() and path.stat().st_size > 10_000
    assert not list(docs.glob('Radon_Monitoring_User_Manual_4.2.1_*.pdf'))
    assert not list(docs.glob('Radon_Monitoring_User_Manual_4.9.0_*.pdf'))
    assert not list(docs.glob('Radon_Monitoring_User_Manual_5.1.0_*.pdf'))
    assert not list(docs.glob('Radon_Monitoring_User_Manual_5.3.0_*.pdf'))
    assert not list(docs.glob('Radon_Monitoring_User_Manual_5.3.2_*.pdf'))
    assert 'Radon_Monitoring_User_Manual_5.5.0' in (LIB / 'web.py').read_text(encoding='utf-8')


def test_frontend_assets_and_ids_are_consistent():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    assert 'assets/core.js?v=__VERSION__' in html
    assert 'assets/app.js?v=__VERSION__' in html
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    assert 'assets/data-management.js?v=__VERSION__' in html
    for removed_id in ('copyHashes', 'hashes', 'runtimeSummary', 'view-expert', 'expertDeviceFacts', 'expertProtocolFacts', 'expertDataFacts'):
        assert f'id="{removed_id}"' not in html
    assert 'data-view="expert"' not in html
    for required_id in ('homeAssistantLocationCard', 'homeAssistantLocationPrivacyMode', 'homeAssistantRoom', 'radonTrafficCard', 'radonTrafficSignal', 'radonTrafficStatus', 'radonTrafficBasis', 'overviewDevice', 'overviewCampaign', 'metricPeak24', 'analysisSummaryText', 'analysisAdvanced', 'view-sites', 'locationRoom', 'haRoomBuilding', 'haRoomPlace', 'gmcmapNav', 'assignFieldset', 'assignmentList', 'runSelfTest', 'selfTestItems', 'locationRoomError', 'locationHeightError'):
        assert f'id="{required_id}"' in html
    assert 'data-view="sites"' in html
    assert 'id="overviewLocation"' not in html
    assert 'id="saveRoomButton"' in html
    assert 'id="locationRoom" name="room"' in html
    assert 'id="locationHeight" name="measurement_height_m"' in html
    assert 'id="currentLocation"' not in html
    assert 'data-view="map"' in html
    sites_section = html.split('id="view-sites"', 1)[1].split('id="view-map"', 1)[0]
    map_section = html.split('id="view-map"', 1)[1].split('id="view-history"', 1)[0]
    assert 'id="locationForm"' in sites_section
    assert re.search(r'id="assignFieldset"[^>]*\bdisabled\b', sites_section)
    assert 'id="assignmentList"' in sites_section
    assert 'id="eventForm"' in sites_section
    assert 'id="locationForm"' not in map_section
    assert 'id="eventForm"' not in map_section
    assert 'block_hashes' not in html
    assert 'runtime_state' not in html
    app_js = (STATIC / 'app.js').read_text(encoding='utf-8')
    for removed_id in ('copyHashes', 'hashes', 'runtimeSummary', 'renderExpert', 'expertDeviceFacts', 'expertProtocolFacts', 'expertDataFacts'):
        assert removed_id not in app_js
    assert 'renderRadonTraffic' in app_js
    assert "location_display_mode" in app_js
    assert "basis_24h_average" in app_js
    assert "event-marker" in app_js
    assert "scope','selection" in app_js
    assert "overviewLocation" not in app_js
    assert "api/locations" not in app_js
    assert "roomsEvents?.render()" in app_js
    assert "systemDiagnostics?.initialize()" in app_js
    rooms_js = (STATIC / 'rooms-events.js').read_text(encoding='utf-8')
    assert "measurement_height_m" in rooms_js
    assert "new URLSearchParams" in rooms_js
    assert "assignFieldset" in rooms_js
    diagnostics_js = (STATIC / 'system-diagnostics.js').read_text(encoding='utf-8')
    assert "api/self-test" in diagnostics_js
    for asset in ('core.js', 'accessibility.js', 'data-management.js', 'rooms-events.js', 'system-diagnostics.js', 'app.js', 'app.css', 'icon.png'):
        assert (STATIC / asset).is_file()


def test_all_html_translation_keys_exist_in_all_locales():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    keys = set(re.findall(r'data-i18n(?:-title|-placeholder|-aria-label)?="([^"]+)"', html))
    assert keys
    for locale_path in LOCALES.glob('*.json'):
        data = json.loads(locale_path.read_text(encoding='utf-8'))
        missing = sorted(keys - data.keys())
        assert not missing, f'{locale_path.name}: missing {missing}'
        for room_key in ('room_name_required', 'saving_room', 'room_saved'):
            assert data.get(room_key), f'{locale_path.name}: missing {room_key}'


def test_analysis_hierarchy_is_translated():
    for locale_path in LOCALES.glob('*.json'):
        data = json.loads(locale_path.read_text(encoding='utf-8'))
        for key in ('basic_statistics', 'basic_statistics_hint', 'advanced_statistics', 'advanced_statistics_hint'):
            assert data.get(key)


def test_javascript_translation_keys_exist_in_all_locales():
    scripts = "\n".join((STATIC / name).read_text(encoding="utf-8") for name in ("app.js", "data-management.js", "rooms-events.js", "system-diagnostics.js"))
    keys = set(re.findall(r"\btr\(['\"]([^'\"]+)['\"]\)", scripts))
    assert keys
    for locale_path in LOCALES.glob('*.json'):
        data = json.loads(locale_path.read_text(encoding='utf-8'))
        missing = sorted(keys - data.keys())
        assert not missing, f'{locale_path.name}: missing dynamic keys {missing}'


def test_home_assistant_configuration_translations_cover_schema():
    import yaml
    config = yaml.safe_load((ROOT / 'config.yaml').read_text(encoding='utf-8'))
    schema_keys = set(config['schema'])
    for translation_path in (ROOT / 'translations').glob('*.yaml'):
        translation = yaml.safe_load(translation_path.read_text(encoding='utf-8')) or {}
        entries = translation.get('configuration', {})
        missing = sorted(schema_keys - set(entries))
        assert not missing, f'{translation_path.name}: missing configuration entries {missing}'
        for key in schema_keys:
            assert str(entries[key].get('name') or '').strip()
            assert str(entries[key].get('description') or '').strip()


def test_repository_root_pytest_configuration_exists():
    repository_root = ROOT.parent
    pyproject = repository_root / 'pyproject.toml'
    assert pyproject.is_file()
    text = pyproject.read_text(encoding='utf-8')
    assert 'gq_radonscan/rootfs/usr/local/lib' in text
    assert 'gq_radonscan/tests' in text


def test_critical_interface_text_is_localised_in_supported_languages():
    english = json.loads((LOCALES / 'en.json').read_text(encoding='utf-8'))
    critical = {
        'analysis_title', 'data_title', 'data_hint', 'delete_entire_database',
        'ha_purge_all_hint', 'verify_purge', 'settings_group_data', 'reports_title',
    }
    for code in ('es', 'fr', 'hr', 'it', 'nl', 'pl'):
        data = json.loads((LOCALES / f'{code}.json').read_text(encoding='utf-8'))
        fallback = sorted(key for key in critical if data.get(key) == english.get(key))
        assert not fallback, f'{code}: English fallback remains for {fallback}'


def test_non_english_locales_do_not_fall_back_to_english_at_scale():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    used = set(re.findall(r'data-i18n(?:-title|-placeholder|-aria-label)?="([^"]+)"', html))
    for name in ('app.js', 'data-management.js', 'rooms-events.js', 'system-diagnostics.js', 'core.js', 'accessibility.js'):
        used.update(re.findall(r"\btr\(['\"]([^'\"]+)['\"]\)", (STATIC / name).read_text(encoding='utf-8')))
    english = json.loads((LOCALES / 'en.json').read_text(encoding='utf-8'))
    technical_or_shared = {
        'Radon Monitoring', 'GQ Radiation World Map', 'GQ World Map', 'Home Assistant',
        'MQTT', 'UTC', 'JSON', 'CSV', 'PDF', 'SHA-256', 'Bq/m³', 'pCi/L', 'SPIR',
        'CPH', 'Firmware', 'Model', 'API', 'Online', 'Offline', 'RESTORE', 'UPLOAD',
    }
    for code in ('es', 'fr', 'hr', 'it', 'nl', 'pl'):
        data = json.loads((LOCALES / f'{code}.json').read_text(encoding='utf-8'))
        same = [key for key in used if data.get(key) == english.get(key) and english.get(key) not in technical_or_shared]
        assert len(same) <= 25, f'{code}: too many English fallbacks ({len(same)}): {sorted(same)[:30]}'
