# 4.4.6

- Fixed the refresh error `can't access property "value", $(...) is null` by making catalogue and filter rendering tolerant of missing or cached interface elements.
- A secondary catalogue/history rendering failure no longer changes a successfully received device status to “Not connected”.
- The connection pill, sidebar status and dashboard system status now remain consistent after manual refreshes.
- Added defensive handling for mixed Ingress HTML/JavaScript versions during add-on updates.

# 4.4.5

- Removed the obsolete Home Assistant entity-selection list and detection button from data management.
- Fixed the web server so the configured Home Assistant administrator token is actually used.
- Long-lived access tokens now connect directly to Home Assistant Core instead of the Supervisor API proxy.
- Purges current and historical RadonScan entity names using both discovered entity IDs and stable entity globs.
- Added visible in-card progress and success/error status for Recorder purge requests.
- Kept navigation inside Radon Monitoring and returns to the app overview after an accepted request.

# Changelog

## 4.4.4

- Dashboard state is rendered before slower catalogue and history requests complete.
- Startup retries every three seconds until the first state response succeeds.
- Regular dashboard refresh shortened to 30 seconds so newly imported USB data appears sooner.
- Removed automatic scientific analysis from initial overview loading.
- Prevented overlapping background refreshes.
- Added one-time automatic reload when an old Home Assistant Ingress iframe uses a different frontend version than the backend.
- Disabled browser caching for JavaScript and CSS assets to avoid stale frontend/backend combinations after updates.


## 4.4.4

- Fixed Home Assistant Recorder purge on installations where administrator-only actions reject the Supervisor token.
- Added optional protected `homeassistant_access_token` configuration.
- Added service discovery and actionable error messages instead of the misleading “service not found” response.
- Kept the local database purge unchanged.

## 4.4.4

- Rebuilt data deletion as two explicit operations: complete local database reset and complete RadonScan Home Assistant history purge.
- Removed selective deletion controls and entity selection to prevent malformed payloads.
- Complete reset now clears all local application data tables, generated reports and map remnants while retaining an empty schema.
- Both operations remain inside the Ingress app and return to the Radon Monitoring overview after success.
- Added complete Home Assistant configuration translations for every option in all shipped languages.

# 4.4.4

- Fixed local database deletion and Home Assistant Recorder purge requests that could still fail with “confirmation required” behind Home Assistant Ingress. Destructive endpoints remain protected by the per-session write-action token; the UI continues to require typed confirmation and a confirmation dialog.
- Expert view now shows the currently configured conversion factor. The factor stored with the latest measurement remains preserved separately in the state payload for scientific traceability.
- Application runtime is no longer marked experimental.

# 4.4.4

- Optionaler Schalter `data_management_enabled` blendet die Datenverwaltung in der Seitenleiste und Oberfläche aus.
- Datenverwaltungs-, Backup- und Recorder-Löschendpunkte sind bei deaktivierter Funktion serverseitig gesperrt.

# 4.4.4

- Fixed destructive deletion confirmation transport by sending the typed token in both JSON and a dedicated request header.
- Backend now accepts canonical confirmation from multiple fields and robust boolean representations, preventing false “confirmation required” errors.
- Added regression tests for header and string-boolean confirmation handling.

# 4.4.4

- Fixed destructive-action confirmation end to end: the browser now sends a canonical server confirmation after local validation, while the backend also accepts an explicit confirmed flag and Unicode-normalised tokens. This resolves persistent “confirmation required” errors caused by character composition, copied whitespace, or mismatched client/server token handling.

# 4.4.4

- improved destructive-action confirmation handling; both LÖSCHEN and PURGE are accepted, including common PURGE typing errors, with clear inline validation

# 4.4.4

- German label “Systemzustand” now contains a discretionary hyphenation point, so it wraps correctly as “System-” / “zustand” on narrow cards without showing an unnecessary hyphen on wider layouts.

# 4.4.4

- Comprehensive responsive layout and spacing audit across all views.
- Prevented card-title, badge, action-button, fact-row and form-field collisions.
- Increased consistent internal spacing while reducing cramped layouts on mobile.
- Stacked facts, status rows, controls and metric cards at narrow breakpoints.
- Improved wrapping for long translations, identifiers, responses and scientific labels.
- Improved modal, report, event, site, table-control and help-card behaviour.

# 4.4.4

- Fixed saving measurement sites in the web interface.
- Async form handlers now retain a stable form reference before awaiting API requests, preventing `event.currentTarget` from becoming `null`.
- Applied the same fix to measurement-site assignment and event forms.

## 4.4.4

- Überschneidungen im Bereich GQ Radiation World Map behoben.
- Kopfzeile, Verbindungsstatus, Messwertvorschau, Aktionsschaltflächen und Faktendarstellung responsiv abgesichert.
- Lange Übersetzungen, IDs, Statusmeldungen und Serverantworten brechen nun kontrolliert um.
- Mobile Darstellung der World-Map-Ansicht für schmale Bildschirme optimiert.

# Changelog

## 4.4.4

- Poisson-basierte, klar begrenzte Schätzung der zählstatistischen Unsicherheit
- wissenschaftliche Qualitätsklassen A–D
- Qualitätsflags ohne automatische Datenlöschung oder Imputation
- Autokorrelationsanalyse und robuste explorative Strukturbrucherkennung
- methodische Metadaten in jeder Analyseantwort
- Kalibrierhistorie mit Labor, Zertifikatreferenz, Unsicherheit und Fälligkeit
- strukturiertes Messkampagnenprotokoll
- Datenbankschema 8 mit verlustfreier Migration
- neue wissenschaftliche Analyse-Kacheln und Hinweise

- removed the Home Assistant `stage: experimental` marker
- added fully revised German and English user manuals for the current interface
- updated installation, operation, World Map, reporting, backup, restore and troubleshooting documentation
- updated the built-in manual endpoint and obsolete version references
- clarified that stable repository presentation does not make the community SPIR decoder an official GQ specification

# 4.4.4

- Added queue-based GQ Radiation World Map uploads with duplicate protection, exponential retry backoff, configurable maximum data age and manual retry of terminal failures.
- Added Home Assistant events for new campaigns and World Map upload success or failure.
- Added configurable analysis time zone with automatic use of the Home Assistant time zone in the web analysis.
- Added robust statistics: geometric mean, geometric standard deviation, interquartile range, median absolute deviation and Theil-Sen trend.
- Added explicit data-quality reasons based on coverage and longest gaps.
- Added conversion-factor history and audit logging.
- Added automated tests for time-zone analysis, robust statistics, database schema, factor history and World Map queue behaviour.
- Removed Python cache files from release artefacts and refreshed configuration translations.

# 4.1.1

- Responsive layout audit and mobile navigation overlay
- Corrected spacing, wrapping and narrow-screen card layouts
- Added translated placeholders and accessible labels
- Completed locale key sets with safe English fallback for newer functions
- Fixed sidebar state race during background refresh

# 4.1.1

- Added optional manual and automatic upload of the latest completed radon reading to the GQ Radiation World Map using the published GMCMap protocol.
- Added masked credential status, upload confirmation, upload history and audit logging.
- Removed floor-plan image upload and map rendering from the web interface and API.
- Retained measurement-site metadata without floor-plan coordinates.

# Changelog

## 4.0.0

- renamed the visible app, panel and interface to **Radon Monitoring**
- changed the interface subtitle to local monitoring for GQ RadonScan devices
- retained the internal slug, database path, MQTT prefix and unique IDs for in-place upgrades
- replaced the former top information tile with a compact measurement and system overview
- added persistent switching between Overview, Analysis and Expert views
- changed 24-hour, 7-day and 30-day calculations to real time windows
- period tiles now explain when a value is not yet meaningfully calculable
- added configurable minimum data coverage and explicit data-gap handling
- added descriptive statistics, percentiles, trend/R², gap-aware threshold runs, daily aggregates, profiles, heatmaps and exposure index
- added explicit device filters for multi-device analysis, histories, measurement sessions, CSV exports and reports
- made overview statistics and MQTT templates device-aware so stored devices cannot receive another device's current values
- added local floor-plan upload and measurement-site markers
- added measurement sessions and event/intervention annotations
- added compact and detailed scientific PDF reports with traceability, canonical data SHA-256 and PDF checksums
- added complete backup ZIP export, restore validation and automatic pre-delete/pre-restore backups
- added selective deletion of local ranges, individual device histories, campaigns, measurements, events, reports and audit history
- added a local administration/audit log
- enabled the Home Assistant Core API and selective Recorder history purge for chosen entities
- restricted the ingress panel to Home Assistant administrators
- extended the SQLite schema to version 4 with automatic migration from version 3
- added Pillow and ReportLab runtime dependencies

## 3.0.1

- fixed `ModuleNotFoundError: No module named 'radonscan3'` at runtime
- added `/usr/local/lib` through Docker `ENV PYTHONPATH`
- exported the same path explicitly from the s6 service
- added a launcher fallback that inserts the package directory into `sys.path`
- no changes to the decoder, database schema, MQTT entities or UI

## 3.0.0

- complete clean rebuild with a new Python package, database schema and ingress interface
- established a single focused completed-hour SPIR data path without compatibility layers
- implemented confirmed read-only SPIR hourly-history decoding
- added campaign/reset-aware SQLite history and deduplication
- added MQTT Discovery entities for completed hourly radon and local averages
- added CSV and diagnostic JSON export
- added eight interface and configuration translations
- added localized user manuals and protocol references
