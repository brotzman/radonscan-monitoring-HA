# Architecture - Radon Monitoring 5.5.11

## Runtime layers

- `service.py`: scan loop, device polling, storage and MQTT publication.
- `device.py` / decoder modules: read-only SPIR transport and record decoding.
- `storage.py`: SQLite schema, migrations and persistence. `overview_selection()` builds one coherent filtered dataset and resolves the applicable room from stored time-based assignments. The module remains a legacy concentration point and should be split incrementally behind tests.
- `room_metadata.py`: canonical room extraction, whitespace normalisation, length/range validation and Ingress fallback merging. This is the single boundary for room request variants.
- `diagnostics.py`: non-destructive operational checks for database integrity, room persistence, report-directory access and external connection state.
- `analysis.py`: deterministic statistical analysis of selected records.
- `reports.py`: PDF composition; chart points are reduced separately from full-data calculations.
- `homeassistant.py`: Home Assistant Core/Supervisor communication, Recorder purge and history verification.
- `gmcmap.py`: GQ Radiation World Map queue and radon-only transport through the documented public `log2.asp` endpoint; outbound fields are limited to `AID`, `GID` and `pCi`.
- `operations.py`: orchestration and audit metadata for destructive database and Recorder workflows.
- `security.py`: central redaction of tokens and sensitive fields.
- `polling.py`: connection-runtime transitions for successful and failed USB scans.
- `web.py`: Ingress HTTP routing and protected API boundary. Feature validation belongs in dedicated modules rather than route branches.

## Browser layers

- `core.js`: translations, formatting, safe browser storage, API wrapper and toast handling.
- `accessibility.js`: focus and accessibility helpers.
- `data-management.js`: reset, purge, purge verification and audit UI.
- `rooms-events.js`: guided room creation/editing, assignment gating, assignment list, event workflow and inline validation.
- `system-diagnostics.js`: System self-test execution and result rendering.
- `app.js`: view state, Overview context, location privacy, charts, analysis and orchestration of feature modules.
- `app.css`: layout and component styling.

New feature areas must be placed in separate modules rather than expanding `app.js`, `web.py` or `storage.py` without bounds. Public API payloads and database behaviour must remain covered by regression tests before code is moved.

## Room workflow invariant

1. Home Assistant is authoritative for place/address and building/location name.
2. The app stores only room and optional measurement height.
3. The request body is canonical; query and encoded headers are fallback-only paths for Ingress failures.
4. A room save is idempotent for the same normalised name.
5. A successful browser workflow requires a persisted room ID from the server.
6. Assignment controls remain disabled until at least one persisted room exists.

## Data and security invariants

- Device communication remains read-only.
- Timestamps are stored in UTC.
- Raw CPH and the factor used for each stored measurement remain reproducible.
- Destructive local reset is transactional and preceded by a safety backup.
- Long-lived Home Assistant tokens are never returned by state, diagnostics or self-test endpoints.
- Error text crossing the HTTP boundary is processed by `safe_error_message`.
- Frontend modules are explicitly allow-listed by the asset server.
- Place/address, building/location name and coordinates are never reverse-geocoded externally.
- The optional World Map view is hidden when external upload is disabled.
- The System self-test uses a rolled-back database savepoint and deletes its temporary report-directory file.

## Compatibility evidence

`COMPATIBILITY.md` separates automated protocol/UI coverage from validation that needs a real Home Assistant installation, WebView, USB device and MQTT broker. Release notes must not describe an environment as field-tested solely because mocked or local HTTP tests pass.

## Recorder purge verification

A successful service call means Home Assistant accepted the request; it is not proof of immediate physical database compaction. Verification queries the History API for recognised Radon entities over a bounded period. Long-term statistics and backend maintenance are documented as separate limitations.
