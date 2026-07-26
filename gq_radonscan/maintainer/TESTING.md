# Testing - Radon Monitoring 4.9.0

## Standard command

Run from the repository root:

```bash
python3 -m pytest
```

Root `pyproject.toml` supplies the app library path and test directory. The app directory also contains compatible local test configuration.

## Test groups

- analysis and statistical regression
- database migration and historical factor preservation
- complete reset, backup, restore and backfill suppression
- Home Assistant purge payload and purge verification
- token and error redaction
- USB disconnect/reconnect runtime state
- GQ World Map queue and manual POST route
- actual web-server static assets and protected endpoints
- three-year hourly database/report performance
- release version, manuals, translations, HTML IDs and asset integrity
- Chromium view checks at 320, 390, 768 and 1440 px
- all eight languages at mobile width
- 200% text scaling, keyboard operation and accessible names
- browser workflows for local reset, Recorder purge and verification

## Additional checks before release

```bash
python3 -m compileall -q gq_radonscan/rootfs/usr/local/lib/radonscan3
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/core.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/accessibility.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/data-management.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/app.js
```

Render both current user manuals and inspect every page. Remove `.pytest_cache`, `__pycache__` and bytecode before packaging.

## Field-test matrix

Automated tests do not replace tests with a real RadonScan and Home Assistant instance. Record results for:

- supported firmware and USB identifiers
- USB removal and reconnection
- app and Home Assistant restart during normal operation
- long-running history import
- MQTT outage and recovery
- GQ World Map outage and queued retry
- Recorder purge on the target Recorder backend
- mobile Home Assistant app WebView
