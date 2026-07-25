# Radon Monitoring 4.4.4 - Technical and Operations Documentation

## 1. Purpose and scope

Radon Monitoring reads completed hourly measurements from the read-only SPIR history of compatible GQ RadonScan devices. It stores the measurements locally in SQLite, publishes Home Assistant entities through MQTT Discovery and provides analysis, scientific reporting, GQ Radiation World Map upload and controlled data administration.

The app does not modify device memory, settings or calibration. It does not reconstruct minute-by-minute readings and does not replace an approved long-term measurement procedure or professional assessment.

## 2. Requirements

- Home Assistant OS or another installation with App/Supervisor support
- supported CPU architecture: `amd64` or `aarch64`
- MQTT service available to apps
- GQ RadonScan connected by USB
- administrator access for the ingress panel
- sufficient free space for SQLite data, reports and backups

The app has been developed against the `RadonScan Re2.02` firmware family. Other compatible firmware may work but should be verified with the Expert view and logs.

## 3. Installation and upgrade

1. Install **Radon Monitoring** from the repository or copy the `gq_radonscan` directory into the local apps directory.
2. Connect the device by USB.
3. Ensure no other application has the serial port open.
4. Provide the MQTT service.
5. Start the app and open the **Radon Monitoring** panel.
6. Confirm that the device, database and MQTT states are healthy.

Leave `serial_port` empty for automatic detection. For a fixed path, prefer a persistent `/dev/serial/by-id/...` device name.

An existing database at `/data/radonscan_v3.sqlite3` is migrated in place. Before schema-changing or destructive operations, create or retain a current backup. The slug `gq_radonscan`, database path, MQTT topic prefix and entity unique IDs are intentionally retained to avoid duplicate entities.

## 4. Views and workflow

### Overview

The Overview is intended for routine monitoring. It shows the latest completed hour, connection state, data age, selected device or site, database state, data quality and the 24-hour, 7-day and 30-day values.

A period value is shown only when:

- the full time span has elapsed; and
- the configured minimum data coverage has been reached.

Otherwise the tile displays a plain-language reason instead of a misleading number.

### Analysis

Analysis provides selectable periods and filters for device, measurement site and campaign. It includes arithmetic and geometric means, median, standard deviation, percentiles, interquartile range, median absolute deviation, Theil-Sen trend, threshold durations, event markers, histogram, daily statistics, hourly and weekday profiles, weekly heatmap, exposure index and data-gap metrics.

Time-related profiles use `analysis_timezone`; raw storage remains in UTC.

### Expert view

The Expert view exposes decoder details, raw CPH values, offsets, SPIR block checksums, firmware information, campaign/import state, conversion-factor history, database integrity and runtime diagnostics. It is intended for troubleshooting and validation rather than daily use.

### History

History provides tabular measurements and exports. Missing hours remain missing and are not interpolated. Device filters should be used when more than one detector is stored in the database.

### Measurement sites, sessions and events

Sites are local metadata; no floor-plan upload is included. A site can be assigned to device-specific measurement sessions. Events such as ventilation, window changes, construction work, moves and outages can be annotated and displayed in analyses and reports.

### GQ Radiation World Map

World Map upload is optional and disabled by default. Account ID and device ID are configured in the app options. A persistent queue prevents duplicate uploads, retries temporary failures and respects the configured maximum age and retry limit.

The app sends the radon measurement through the supported GQ upload protocol. It does not send GPS coordinates. Public location information is controlled in the user's GQ device profile. Enabling the feature causes measurement data and identifiers to leave the local Home Assistant system.

### Reports

Compact and detailed PDF reports are generated locally. Depending on the selected profile, a report contains:

- device, period, site and session information
- result summary and data coverage
- descriptive and robust statistics
- threshold and data-gap information
- charts, profiles and documented events
- firmware, conversion factor and software version
- method, limitations and interpretation notes
- SHA-256 checksum of the selected canonical measurement data

Generated reports are scientific documentation aids, not official certificates.

### Data management

The interface can:

- create a complete backup ZIP with database, reports and manifest
- download CSV and diagnostics JSON
- preview deletion targets
- delete a time range, device history, campaign, events, reports or audit entries
- perform a full local reset
- integrity-check and restore a supported SQLite database or app backup

An automatic local backup is created before destructive operations. The physical detector history is never erased by the app.

### Home Assistant Recorder history

With `homeassistant_api: true`, the app can find likely Radon Monitoring entities and invoke `recorder.purge_entities` for explicitly selected entities. This affects Home Assistant Recorder only; it does not delete the local SQLite data or device history.

## 5. Measurement and calculation model

Confirmed read areas:

- `0x1FC000`: completed raw hourly CPH values
- `0x1FD000`: diagnostic or administrative data; not published as the normal measurement
- `0x1FE000`: hour records, 14 bytes each: `AA 55 + seconds (BE32) + 8 payload bytes`

Conversion:

```text
Bq/m³ = raw CPH × factor_bq_m3_per_cph
```

The default factor is `1.530`. It is configurable and is stored with each measurement so historic data retains the factor used at import time. Factor changes are logged in the factor history.

## 6. Main configuration options

| Option | Default | Purpose |
|---|---:|---|
| `scan_interval` | 300 s | Interval between read-only polls |
| `serial_port` | empty | Automatic detection or fixed device path |
| `serial_timeout_seconds` | 3.0 s | Serial response timeout |
| `factor_bq_m3_per_cph` | 1.530 | Conversion factor stored per measurement |
| `minimum_data_coverage_percent` | 95 | Coverage required for period values |
| `backfill_history` | true | Import completed history from the detector |
| `history_retention_days` | 1095 | Local measurement retention |
| `preferred_unit` | Bq/m3 | Display and MQTT unit |
| `analysis_timezone` | auto | Time zone for daily and weekly analyses |
| `language` | auto | Interface and manual language |
| `report_author` | empty | Optional report author |
| `report_organisation` | empty | Optional organisation in reports |
| `report_disclaimer` | empty | Optional additional report notice |
| `gmcmap_enabled` | false | Enable World Map functions |
| `gmcmap_auto_upload` | false | Upload queued values automatically |
| `gmcmap_upload_interval_minutes` | 60 | Automatic upload interval |
| `gmcmap_max_age_hours` | 72 | Maximum age for queued automatic uploads |
| `gmcmap_retry_limit` | 8 | Maximum upload attempts |
| `diagnostic_logging` | false | Additional diagnostic messages |
| `log_level` | info | Application log level |

## 7. Backup and restore procedure

Before a major update or extensive deletion:

1. Stop unnecessary writes and confirm sufficient free space.
2. Create a complete backup ZIP from Data management.
3. Download the backup outside Home Assistant.
4. Keep the SHA-256 value or backup manifest with the file.
5. After an update, verify database integrity, latest timestamp and device count.

Restore validates the uploaded SQLite database before replacement and creates a pre-restore backup. If a restore fails, retain the original backup and inspect the app log before retrying.

## 8. Troubleshooting

### Device not found

Check USB connection, host permissions, `serial_port`, and whether another process has opened the port. Prefer a persistent by-id path if automatic device order changes.

### No new measurement

The app publishes only completed hours. Check the timestamp of the last stored value, the detector clock/index state, the Expert view and the service log.

### Period average unavailable

The required time span or minimum coverage has not yet been reached. Review missing hours and the longest data gap in Analysis.

### World Map upload fails

Verify account ID, device ID, internet access, queue state, last server response, maximum-age setting and retry limit. Avoid repeatedly changing identifiers while queued items exist.

### Report generation fails

Check free space, database integrity, the selected period and whether a valid PDF can be created for a smaller range.

### Upgrade issue

Restart the app once, review migration log entries and compare database counts with the pre-upgrade backup. Do not delete the backup until several new hours have been stored successfully.

## 9. Documentation supplied with the app

The Help view serves current **Radon Monitoring 4.4.4** user manuals in German and English. Other interface languages fall back to the English manual. Separate localized protocol-reference PDFs remain bundled because the read-only SPIR protocol has not changed with the application version.

## 10. Safety and scientific limitations

Radon Monitoring is a community implementation. Removal of the Home Assistant experimental-stage label means the app is presented as a normal repository release; it does not turn the reverse-engineered device protocol into an official GQ specification.

Short-term concentrations, threshold durations, correlations and generated reports must not be used as the sole basis for medical, legal, workplace or building decisions. Statutory reference values generally relate to long-term averages, not an individual hourly reading. Use an appropriate measurement duration and consult qualified authorities or professionals where required.


### Home Assistant Recorder-Verlauf löschen

Die Aktion `recorder.purge_entities` ist in aktuellen Home-Assistant-Versionen administratorgeschützt. Falls der Supervisor-Token abgewiesen wird, in Home Assistant unter **Profil → Sicherheit → Langlebige Zugriffstoken** einen Token eines Administrators erstellen und in der App-Option `homeassistant_access_token` hinterlegen. Der Token wird nicht in der Weboberfläche oder in Diagnoseausgaben angezeigt.
