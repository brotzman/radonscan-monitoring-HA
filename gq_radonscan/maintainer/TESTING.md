# Testing - Radon Monitoring 5.5.3

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
- Radon-only GMCMap request contract: `rdlog.asp` with exactly `AID`, `GID` and `pCi`; no `CPM`, `ACPM` or `uSV`
- actual web-server static assets and protected endpoints
- three-year hourly database/report performance
- release version, manuals, translations, HTML IDs and asset integrity
- Chromium view checks at 320, 390, 768 and 1440 px
- all eight languages at mobile width
- 200% text scaling, keyboard operation and accessible names
- browser workflows for local reset, Recorder purge and verification
- filter-coherent Overview state/history requests for device and campaign with automatic room resolution
- 24-hour Radon traffic-light assessment and provisional hourly fallback
- precise, reduced and hidden location modes including coordinate units
- read-only Home Assistant place/building source data and room-only save payloads
- JSON, URL-encoded, chunked, header and query fallback room requests through the real HTTP server
- idempotent room saves, duplicate prevention and decimal-comma measurement height
- guided room/assignment workflow, inline field errors and visible assignment cards
- non-destructive System self-test and protected POST endpoint
- chart event markers, dedicated Rooms & events navigation and hidden disabled World Map
- plain-language Analysis summary with collapsed advanced diagnostics

## Additional checks before release

```bash
python3 -m compileall -q gq_radonscan/rootfs/usr/local/lib/radonscan3
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/core.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/accessibility.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/data-management.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/rooms-events.js
node --check gq_radonscan/rootfs/usr/local/lib/radonscan3/static/system-diagnostics.js
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
- Confirm in a real GMCMap account that new RadonScan uploads appear only on the radon map and do not create a 0 CPM radioactivity point
- Recorder purge on the target Recorder backend
- mobile Home Assistant app WebView
- complete room create/edit/assign flow and built-in System self-test result

The detailed automated-versus-field matrix is maintained in `COMPATIBILITY.md`.
