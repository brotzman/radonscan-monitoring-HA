# Changelog

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
