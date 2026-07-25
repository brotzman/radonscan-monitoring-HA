# Changelog

All notable changes to Radon Monitoring are documented here. Versions follow semantic versioning.

## 4.6.0 - Stability, documentation and maintainability

- Rebuilt the German and English user manuals for the current interface and feature set.
- Cleaned and normalised the complete changelog so each change is assigned to one release only.
- Split reusable browser utilities, API handling and toast/error normalisation into `static/core.js`.
- Structured the Analysis view into clearly labelled core and advanced statistical sections.
- Added translated section descriptions in all eight interface languages.
- Added release-integrity, translation, HTML-ID, asset-loading and migration regression tests.
- Added architecture, testing and release-checklist documentation for maintainers.
- Clarified protocol-reference versioning: protocol reference 3.0.0 remains separate from the app version.
- No database-schema change; existing 4.x databases remain compatible.

## 4.5.0 - Statistical analysis expansion

- Added effective sample size and estimated correlation duration.
- Added moving-block-bootstrap confidence intervals for mean and median.
- Added Mann-Kendall trend diagnostics and Sen slope.
- Added skewness, excess kurtosis, mean-to-median ratio and Freedman-Diaconis histogram bins.
- Added 10% trimmed mean and sensitivity comparison.
- Added rolling 24-hour median and interquartile band.
- Added continuous threshold-event metrics and concentration-class shares.
- Hardened analysis spacing, wrapping and mobile layouts down to 320 px.

## 4.4.7 - Recorder purge endpoint fix

- Fixed an internal server error caused by an incorrect Home Assistant entity-method name.
- Added regression coverage for the Recorder purge endpoint.

## 4.4.6 - Refresh and status consistency

- Made catalogue and filter rendering tolerant of missing or cached interface elements.
- Prevented secondary data-loading failures from changing a valid device status to “Not connected”.
- Kept connection indicators consistent after manual refreshes.

## 4.4.5 - Home Assistant Recorder purge rebuild

- Removed obsolete entity-selection controls.
- Used the configured Home Assistant administrator token for administrator-only Recorder actions.
- Connected long-lived access tokens directly to Home Assistant Core.
- Added stable entity globs and visible progress/error status.
- Kept navigation inside Radon Monitoring after accepted actions.

## 4.4.4 - Loading and cache behaviour

- Rendered dashboard state before slower catalogue and history requests.
- Added startup retries and 30-second overview refresh.
- Prevented overlapping background refreshes.
- Added frontend/backend version mismatch reload protection.
- Disabled long-lived caching of JavaScript and CSS assets.

## 4.4.3 - Administrator token support

- Added optional protected `homeassistant_access_token` configuration.
- Added service discovery and actionable Recorder purge errors.

## 4.4.2 - Simplified destructive data management

- Rebuilt deletion as complete local database reset and complete RadonScan Recorder-history purge.
- Removed selective deletion controls that produced malformed payloads.
- Added complete Home Assistant option translations.

## 4.4.1 - Confirmation and factor display

- Simplified backend confirmation handling behind Home Assistant Ingress.
- Expert view now distinguishes the configured conversion factor from the factor stored with historical measurements.

## 4.4.0 - Data-management feature switch

- Added `data_management_enabled` to hide the navigation item and disable the related endpoints server-side.

## 4.3.x - Scientific workflow and interface hardening

- Added scientific quality classes, count-statistical uncertainty, quality flags, autocorrelation and exploratory change-point analysis.
- Added calibration history and structured campaign protocols.
- Improved responsive layouts, spacing, long-label wrapping and form reliability.
- Corrected firmware display and German hyphenation.

## 4.2.x - Reliability and documentation

- Added persistent World Map queue, duplicate protection and retry logic.
- Added local-time analysis, robust statistics and factor history.
- Removed the Home Assistant experimental-stage marker.
- Added revised German and English manuals.

## 4.1.x - World Map and responsive interface

- Replaced local floor-plan upload with optional GQ Radiation World Map upload.
- Added upload history and responsive interface corrections.

## 4.0.0 - Radon Monitoring redesign

- Renamed the app to Radon Monitoring.
- Added Overview, Analysis and Expert views.
- Added time-based averages with minimum-duration and coverage checks.
- Added reports, measurement sites, events, backup/restore and controlled data management.
- Preserved the existing slug, database path and MQTT identities for compatible upgrades.
