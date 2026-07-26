# Radon Monitoring 4.9.0 - App documentation

## Purpose

Radon Monitoring reads completed hourly records from compatible GQ RadonScan devices using read-only SPIR commands. It stores measurements locally, exposes selected values to Home Assistant through MQTT and provides analysis, reporting and controlled data-management workflows.

The app is an orientation and documentation tool. It does not turn a consumer monitor into a certified regulatory measurement system.

## First start

1. Connect the RadonScan by USB.
2. Ensure an MQTT broker is available to Home Assistant.
3. Leave `serial_port` empty or set it to `auto` for discovery. For a stable fixed assignment, prefer a `/dev/serial/by-id/...` path.
4. Start the app and open its Ingress panel.
5. Check the connection state, firmware, current configured factor and first completed hourly value.

Only completed hours are imported. A newly connected device may therefore remain without a current value until a completed record is available.

## Views

### Overview

Shows the latest completed value, age, measurement site, raw CPH, stored sample count, device/MQTT state and 24-hour, 7-day and 30-day summaries. A period card shows a reason instead of a number when duration or coverage is insufficient.

### Analysis

Contains basic and advanced statistics, distribution and trend diagnostics, daily and weekday profiles, rolling robust values, threshold events and a weekly heatmap. Missing values are not imputed and flagged observations are not silently deleted.

### Expert

Shows protocol, decoder, firmware, port, checksums, database details, runtime state and factor history. The currently configured conversion factor is intentionally separate from the factor stored with a historical measurement.

### GQ Radiation World Map

Uploads are optional and disabled by default. The persistent queue retries temporary failures and prevents duplicate publication. The app sends the radon value and GQ identifiers required by the configured protocol; public location settings are managed in the GQ account.

### Measurement sites and events

Sites, sessions and events are local metadata. They can document room, building, placement, ventilation, interventions and device changes without modifying the original measurement.

### Reports

Compact and detailed PDF reports include selected metadata, data completeness, statistics, method notes and SHA-256 checksums. Multi-year time-series charts are reduced to a bounded, peak-preserving representation for readability and performance. Descriptive statistics, threshold calculations and data checksums continue to use every selected record.

### Data management

The whole area can be disabled with `data_management_enabled`.

- **Backup:** creates a copy of the app database.
- **Restore:** validates an uploaded SQLite database before replacing the active database.
- **Complete local reset:** creates an automatic safety backup, clears app-owned measurement and metadata tables transactionally, verifies database integrity and suppresses immediate re-import of the deleted device history.
- **Home Assistant Recorder purge:** submits all recognised RadonScan entities and stable Radon name patterns to `recorder.purge_entities` using an optional administrator token.
- **Verification:** checks recent Home Assistant History API results after a purge request. The result is informative: Recorder maintenance may continue asynchronously and separately stored long-term statistics may remain.

## Security

`homeassistant_access_token` is write-only from the app's perspective. The interface shows only whether it is configured. Central redaction removes bearer tokens and known secret fields from diagnostics and error messages. The token is not written into scientific reports or app database backups.

Use a dedicated long-lived Home Assistant token and remove it when Recorder maintenance is no longer required.

## Configuration groups

### Device and measurement

- `serial_port`
- `scan_interval`
- `factor_bq_m3_per_cph`
- `backfill_history`
- `history_retention_days`
- `preferred_unit`

### Statistics and assessment

- `warning_threshold_bq_m3`
- `danger_threshold_bq_m3`
- `minimum_data_coverage_percent`
- `analysis_timezone`

### GQ Radiation World Map

- `gmcmap_enabled`
- `gmcmap_auto_upload`
- `gmcmap_account_id`
- `gmcmap_device_id`
- `gmcmap_upload_interval_minutes`
- `gmcmap_max_age_hours`
- `gmcmap_retry_limit`

### Reports

- `report_author`
- `report_organisation`
- `report_disclaimer`

### Data management and diagnostics

- `data_management_enabled`
- `homeassistant_access_token`
- `diagnostic_logging`
- `language`

## Troubleshooting

### Device not connected

Check USB mapping, permissions, configured port and whether another process has opened the serial device. Review the Expert view and app log.

### New USB data is not visible

Use Refresh once. The compact state is loaded before history and catalogue data, and the view updates automatically every 30 seconds. Only completed hours are displayed.

### Old interface after an update

Stop and start the app, close the existing Ingress panel and reopen it. Versioned assets and a frontend/backend mismatch check prevent most stale combinations.

### Recorder purge fails

Confirm that the administrator token is valid, that the Recorder integration is loaded and that the token belongs to an administrator. The app connects long-lived tokens directly to Home Assistant Core.

### Purge verification reports remaining history

Recorder deletion is asynchronous on some systems. Wait and verify again. A remaining-history result can also indicate an entity that was not included or history retained outside the checked period. Long-term statistics are a separate Home Assistant data path.

### Restore is rejected

The uploaded file must be a readable SQLite database with a compatible schema. The active database remains unchanged when validation fails.

## Testing and release information

From the repository root:

```bash
python3 -m pytest
```

Version 4.9.0 includes tests for web assets, API routes, destructive workflows, token redaction, USB reconnect state, database migrations, damaged restores, three years of hourly report data, responsive layouts, all eight interface languages, keyboard operation and 200% text scaling.

Real-device and real-Home-Assistant field testing remains necessary for USB hardware variations, Home Assistant upgrades and Recorder backends.
