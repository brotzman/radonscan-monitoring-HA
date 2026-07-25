import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'rootfs/usr/local/lib/radonscan3'
STATIC = LIB / 'static'
LOCALES = LIB / 'locales'


def test_release_versions_are_consistent():
    assert 'version: 4.6.0' in (ROOT / 'config.yaml').read_text(encoding='utf-8')
    assert 'BUILD_VERSION="4.6.0"' in (ROOT / 'Dockerfile').read_text(encoding='utf-8')
    assert '__version__ = "4.6.0"' in (LIB / '__init__.py').read_text(encoding='utf-8')
    assert 'Radon Monitoring 4.6.0' in (ROOT / 'README.md').read_text(encoding='utf-8')


def test_current_manuals_exist_and_obsolete_manuals_are_removed():
    docs = ROOT / 'rootfs/usr/local/share/radonscan3/docs'
    for lang in ('de', 'en'):
        path = docs / f'Radon_Monitoring_User_Manual_4.6.0_{lang}.pdf'
        assert path.is_file() and path.stat().st_size > 10_000
    assert not list(docs.glob('Radon_Monitoring_User_Manual_4.2.1_*.pdf'))
    assert 'Radon_Monitoring_User_Manual_4.6.0' in (LIB / 'web.py').read_text(encoding='utf-8')


def test_frontend_assets_and_ids_are_consistent():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    assert 'assets/core.js?v=__VERSION__' in html
    assert 'assets/app.js?v=__VERSION__' in html
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    for asset in ('core.js', 'app.js', 'app.css', 'icon.png'):
        assert (STATIC / asset).is_file()


def test_all_html_translation_keys_exist_in_all_locales():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    keys = set(re.findall(r'data-i18n(?:-title|-placeholder|-aria-label)?="([^"]+)"', html))
    assert keys
    for locale_path in LOCALES.glob('*.json'):
        data = json.loads(locale_path.read_text(encoding='utf-8'))
        missing = sorted(keys - data.keys())
        assert not missing, f'{locale_path.name}: missing {missing}'


def test_analysis_hierarchy_is_translated():
    for locale_path in LOCALES.glob('*.json'):
        data = json.loads(locale_path.read_text(encoding='utf-8'))
        for key in ('basic_statistics', 'basic_statistics_hint', 'advanced_statistics', 'advanced_statistics_hint'):
            assert data.get(key)
