# Architecture - Radon Monitoring 5.3.1

## Runtime layers

- `service.py`: scan loop, device polling, storage and MQTT publication.
- `device.py` / decoder modules: read-only SPIR transport and record decoding.
- `storage.py`: SQLite schema, migrations and persistence. `overview_selection()` builds one coherent filtered dataset for device and campaign, resolves the applicable room from stored time-based assignments and prevents mixed-room values in the Overview. This remains the largest legacy module and should be split incrementally without changing public behaviour.
- `analysis.py`: deterministic statistical analysis of selected records.
- `reports.py`: PDF composition; chart points are reduced separately from full-data calculations.
- `homeassistant.py`: Home Assistant Core/Supervisor communication, Recorder purge and history verification.
- `gmcmap.py`: GQ Radiation World Map queue and transport.
- `operations.py`: orchestration and audit metadata for destructive database and Recorder workflows.
- `security.py`: central redaction of tokens and sensitive fields.
- `polling.py`: connection-runtime transitions for successful and failed USB scans.
- `web.py`: Ingress HTTP routing and protected API boundary.

## Browser layers

- `core.js`: translations, formatting, safe browser storage, API wrapper and toast handling.
- `accessibility.js`: focus and accessibility helpers.
- `data-management.js`: reset, purge, purge verification and audit UI.
- `app.js`: view state, persistent device/campaign Overview context, automatic room rendering, Home Assistant location privacy rendering, chart event annotations and remaining feature controllers.
- `app.css`: layout and component styling.

New feature areas should be placed in separate modules rather than expanding `app.js`, `web.py` or `storage.py` without bounds.

## Data and security invariants

- Device communication remains read-only.
- Timestamps are stored in UTC.
- Raw CPH and the factor used for each stored measurement remain reproducible.
- Destructive local reset is transactional and preceded by a safety backup.
- Long-lived Home Assistant tokens are never returned by state or diagnostics endpoints.
- Error text crossing the HTTP boundary is processed by `safe_error_message`.
- Frontend modules are explicitly allow-listed by the asset server.
- Place/address, building/location name and coordinate details are read from Home Assistant and never reverse-geocoded externally; only room and measurement height are manually maintained. `location_display_mode` controls full, reduced or hidden presentation.
- The optional World Map view is hidden when external upload is disabled, while local rooms, assignments and events remain available independently.

## Recorder purge verification

A successful service call means Home Assistant accepted the request; it is not proof of immediate physical database compaction. Verification queries the History API for recognised Radon entities over a bounded period. Long-term statistics and backend maintenance are documented as separate limitations.
