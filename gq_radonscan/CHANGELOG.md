# Changelog

## 5.5.10 - Two-decimal Radon display

- Show Bq/m³ concentrations with two visible decimal places throughout the main interface, including the current value, Overview cards, Analysis facts, history tables, daily summaries, threshold labels and GMCMap history.
- Keep pCi/L display precision at three decimal places.
- Set Home Assistant MQTT Discovery `suggested_display_precision` to 2 for the hourly, 24-hour and 7-day Bq/m³ sensors.
- Preserve the full stored calculation precision; this release changes presentation only and does not round database values or statistical calculations.
- Keep all timestamp reconstruction, zero-count confirmation, MQTT compatibility, radon-only GMCMap and fixed serial-port behaviour from 5.5.9.
- No database-schema change.

## 5.5.4 - Correct public GMCMap upload endpoint

- Corrected the World Map target from the unavailable `rdlog.asp` URL to GMCMap's documented public `log2.asp` submission endpoint.
- Keep RadonScan uploads radon-only by sending exactly `AID`, `GID` and `pCi`; `CPM`, `ACPM` and `uSV` remain deliberately absent.
- Added explicit HTTP status/body recording so endpoint and account errors are visible in the upload history.
- Updated all interface languages, maintainer documentation, user manuals and request-level regression tests.
- Retained the fixed-port and safer serial-discovery changes introduced in 5.5.3.
- Kept the database schema, queue format, MQTT identifiers and stored measurements unchanged.

## 5.5.3 - Fixed RadonScan port and safer serial discovery

- Treat a configured `serial_port` as exclusive instead of appending and probing every serial device on the Home Assistant host.
- Set the installation default to `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` and migrate a retained empty option to that path during the upgrade.
- Keep an explicit `auto` value automatic; automatic discovery now skips recognisable Sonoff, ITEAD, Zigbee, Z-Wave and `/dev/ttyAMA*` devices.
- Prefer stable `/dev/serial/by-id/` aliases and de-duplicate aliases that resolve to the same physical serial port.
- Classify disconnected states as port busy, port missing, permission denied, no response, wrong device, read error, no eligible ports or no RadonScan detected.
- Show the checked port and translated connection diagnosis under Devices & System.
- Replace the obsolete fixed `Starting Radon Monitoring 4.0` log line with the actual package version.
- Keep the database schema, MQTT identifiers, measurements, analysis and Radon-only GMCMap upload unchanged.

## 5.5.2 - Radon-only GQ World Map uploads

- Switched GQ World Map uploads from the generic `log2.asp` radiation endpoint to the dedicated `rdlog.asp` radon endpoint.
- Removed the artificial `CPM=0` field and now submit only `AID`, `GID` and `pCi` for RadonScan measurements.
- Explicitly prevent `CPM`, `ACPM` and `uSV` from being included in RadonScan uploads so new zero-valued radioactivity entries are no longer created.
- Added a visible **Radon only** upload mode and updated the protocol notice in all eight interface languages.
- Added request-level regression tests that verify the endpoint and exact submitted query fields.
- Kept the database schema, local measurements, queue format and Home Assistant identifiers unchanged.

## 5.5.1 - Mobile UI polish and compact statistics cards

- Added a focused **UI polishing** pass for narrow screens and Home Assistant mobile WebViews.
- Made Overview, Analysis and Data statistics cards more compact with reduced padding, tighter typography and better use of two-column layouts on small screens before falling back to a single column on very narrow displays.
- Tightened panel spacing, section-heading spacing and chart legend spacing in the statistical views to reduce scrolling without sacrificing readability.
- Improved mobile readability of fact grids with balanced label/value sizing, safer wrapping and clearer stacking behaviour.
- Refined the Advanced statistics details header so long helper text wraps cleanly on smaller screens.
- Kept all data structures, API routes and statistical calculations unchanged; this is a presentation-only refinement release.

- Reordered the **Analysis** view into concentration level, thresholds, distribution, development, data quality and event impact sections; removed the separate **Time patterns** card from Advanced statistics and added new rolling, percentile and comparison statistics.
- Reworked **Rooms & events** into a guided two-step workflow: create or edit a room first, then assign a device and time period.
- Disabled the assignment form until at least one room exists and added clear next-step empty states.
- Added inline validation beside room, measurement-height, assignment and event fields instead of relying only on transient toast messages.
- Added a URL query fallback for room name, measurement height and edit ID in addition to JSON, URL-encoded and chunked request-body handling. This covers Ingress variants that forward an empty body and remove custom headers.
- Made repeated room submissions idempotent and prevented case-insensitive duplicate room names.
- Added visible measurement-assignment cards so saved room/device/time relationships can be verified directly.
- Added a non-destructive **System self-test** for API availability, SQLite integrity, room insert/read/rollback, report-directory writes, RadonScan, MQTT and Home Assistant connectivity.
- Split room/event browser logic into `rooms-events.js`, system checks into `system-diagnostics.js`, and request normalisation/self-test logic into dedicated Python modules.
- Added `maintainer/COMPATIBILITY.md` to distinguish automated contract tests from required real-device and Home Assistant field tests.
- Kept schema version 8 and all existing database, MQTT and Home Assistant identifiers unchanged.

## 5.3.1 - Reliable room saving

- Fixed room creation through Home Assistant Ingress when frontend and backend assets briefly differ during an upgrade.
- Added named form fields, whitespace normalisation, local validation and a legacy `name` alias without storing duplicate location metadata.
- Room creation now updates the visible room list immediately and no longer depends on a successful Home Assistant status refresh.
- Removed compiled Python caches from the release archive to prevent stale bytecode after updates.

All notable changes to Radon Monitoring are documented here. Versions follow semantic versioning.

## 5.3.0 - Home Assistant sourced location and room-only metadata

- Simplified the Overview context to device and campaign; removed the measurement-site selector and resolve the applicable room automatically from time-based assignments.
- Show the resolved room and optional measurement height directly beneath the Home Assistant location card.
- Changed Local metadata to **Rooms & events** with read-only place/address and building/location data from Home Assistant.
- Reduced manual room metadata to exactly room name and measurement height; legacy building, floor, room type, map position and notes fields are no longer editable and are cleared when a room is saved.
- Added Home Assistant location data to the catalogue API so the room form can show its authoritative source without external geocoding.
- Kept the Radon traffic light based on the 24-hour mean with provisional hourly fallback, the 24-hour peak, event markers, visible chart gaps and collapsed advanced Analysis.
- Added degree units and cardinal directions to coordinates, for example `51,60176° N, 7,45410° E`.
- Updated reports to include the Home Assistant location/building, room and measurement height as separate traceability fields.
- Updated all eight interface languages, automated tests and the German and English user manuals.
- No database-schema change; existing 4.x, 5.0.0, 5.1.0 and 5.2.0 databases remain compatible.

## 5.1.0 - Overview location, Radon traffic light and streamlined navigation

- Added a responsive Home Assistant location card to the Overview.
- Read location name or locally supplied address, coordinates, elevation, country and time zone from the local Home Assistant Core configuration.
- Added an explicit privacy note and no external reverse-geocoding dependency.
- Added graceful fallback to the Home Assistant location name when no postal address is exposed.
- Added a Radon traffic light that classifies the latest completed hourly value using the configured warning and danger thresholds.
- Removed the complete Expert view from the interface and sidebar; operational data remains consolidated under Devices & System and Settings.
- Added backend, localisation, integrity and responsive browser regression tests.
- Updated release metadata and the German and English user manuals to version 5.1.0.
- No database-schema change; existing 4.x and 5.0.0 databases remain compatible.

## 5.0.0 - Streamlined Expert view

- Removed the Block checksums and Runtime status cards from the Expert view.
- Removed the associated clipboard control and frontend render handlers.
- Kept detailed technical information available through the diagnostics download.
- Updated release metadata, automated integrity checks and the German and English user manuals to version 5.0.0.
- No database-schema change; existing 4.x databases remain compatible.

## 4.9.0 - Reliability, verification and maintainability

- Split destructive-data workflows into `operations.py` and the browser code into `data-management.js`.
- Added reusable security helpers that redact bearer tokens and other sensitive values from errors and diagnostics.
- Added Home Assistant Recorder purge verification through the History API, with an explicit limitation notice for long-term statistics and asynchronous database maintenance.
- Added deterministic USB disconnect/reconnect state handling and regression tests.
- Fixed the manual GQ Radiation World Map upload route so it is handled as a protected POST request.
- Fixed the static asset allow-list so `core.js`, `accessibility.js` and `data-management.js` are served by the real web server.
- Added safe browser-storage access for Home Assistant WebViews and privacy-restricted browser contexts.
- Added a missing fast-state refresh function used after destructive operations.
- Added peak-preserving chart reduction for multi-year PDF reports while retaining all records for descriptive statistics, threshold calculations and checksums.
- Bounded exploratory change-point diagnostics for multi-year datasets and documented the diagnostic sample size in results.
- Added root-level `pyproject.toml` and `pytest.ini`; the complete test suite now runs from the repository root with `python3 -m pytest`.
- Added browser end-to-end tests for database reset, Recorder purge and purge verification.
- Added responsive Chromium checks at 320, 390, 768 and 1440 pixels, all eight interface languages, 200% text scaling, keyboard operation and accessible control names.
- Added actual web-server integration tests, token-redaction tests, three-year report performance tests and World Map route tests.
- Completed native Home Assistant option translations for German, English, Spanish, French, Croatian, Italian, Dutch and Polish.
- Rebuilt the German and English user manuals for version 4.9.0.
- No database-schema change; existing 4.x databases remain compatible.

## 4.8.0 - Safer destructive operations and test configuration

- Added result reports and operation IDs for complete local database deletion and Home Assistant Recorder purge.
- Added automatic safety backup, transactional reset, post-reset integrity checks and backfill suppression.
- Added responsive operation-result panels and standard test configuration.

## 4.7.0 - Accessibility and responsive hardening

- Reorganised settings into functional groups.
- Added skip-to-content navigation, visible keyboard focus and reduced-motion support.
- Added responsive browser checks and damaged-backup regression coverage.

## 4.6.0 - Documentation and consolidation

- Rebuilt the user manuals and normalised release documentation.
- Split reusable browser utilities into `core.js`.
- Structured Analysis into basic and advanced statistical sections.

## 4.5.0 - Statistical analysis expansion

- Added effective sample size, moving-block-bootstrap confidence intervals, Mann-Kendall diagnostics and Sen slope.
- Added rolling robust statistics, concentration classes and continuous threshold-event metrics.

## 4.4.x - Data-management and Recorder reliability

- Added the data-management feature switch and administrator-token support.
- Rebuilt complete local reset and complete RadonScan Recorder purge.
- Corrected refresh, cache, confirmation and configured-factor behaviour.

## 4.3.x - Scientific workflow and interface hardening

- Added scientific quality classes, count-statistical uncertainty, quality flags, autocorrelation and exploratory change-point analysis.
- Added calibration history and structured campaign protocols.
- Improved responsive layouts, spacing, form reliability and terminology.

## 4.2.x - Queueing, time zones and manuals

- Added persistent World Map queueing, duplicate protection and retry logic.
- Added local-time analysis, robust statistics and factor history.
- Removed the Home Assistant experimental-stage marker and updated manuals.

## 4.1.x - GQ Radiation World Map

- Replaced local floor-plan upload with optional GQ Radiation World Map upload.
- Added upload history and responsive interface corrections.

## 4.0.0 - Radon Monitoring redesign

- Renamed the app to Radon Monitoring.
- Added Overview, Analysis and Expert views.
- Added real time-window averages, reports, measurement sites, events, backup/restore and controlled data management.

## 3.0.x - Local RadonScan foundation

- Added read-only SPIR history import, local SQLite storage, MQTT Discovery and a compact local web interface.
