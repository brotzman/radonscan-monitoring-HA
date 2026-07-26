# Radon Monitoring 5.2.0 - App documentation

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

The context bar selects a **device**, **measurement site** and **campaign**. The selection is retained locally in the browser. Applying it reloads the latest measurement, 24-hour, 7-day and 30-day summaries, selected sample count, 24-hour peak and chart from the same filtered record set. This avoids combining values from different devices or rooms.

The Radon traffic light uses the 24-hour mean when the period has sufficient duration and coverage. Before that condition is met, it uses the latest completed hourly value and labels the result as provisional. The exact assessment basis, data coverage and configured warning/danger thresholds are shown with the signal.

The fourth overview metric is the maximum observed value in the latest 24-hour window, with measurement time and coverage. Documented events are drawn as vertical markers in the chart. Gaps longer than 90 minutes split the line so missing data is not visually interpolated.

The Home Assistant location card reads only local Core configuration values. In full mode it shows the address, or the configured location name when no address is available, plus coordinates, elevation, country and time zone. Coordinates include degrees and cardinal directions, for example `51,60176° N, 7,45410° E`. No reverse geocoding is performed and no location values are sent to an external geocoding service.

`location_display_mode` controls disclosure:

- `full`: address/location name and precise coordinates
- `reduced`: location name and coordinates rounded to two decimals
- `hidden`: card omitted from the Overview

### Analysis

Analysis starts with a plain-language summary of trend direction, warning-threshold share, danger-threshold share and data coverage. Basic statistics remain immediately visible. Scientific quality, counting uncertainty, effective sample size, confidence intervals, autocorrelation, distribution diagnostics and sensitivity results are grouped under a collapsed advanced section.

The analysis time series includes documented events and visible gaps. Missing values are not imputed and flagged observations are not silently deleted. Statistical significance does not establish causality; event notes and measurement conditions still require professional interpretation.

### Measurement sites & events

This dedicated view contains sites, device-to-site assignments/sessions and event documentation. It can record room, building, floor, placement height, ventilation, interventions, building work, outages and device changes without altering the original measurement values.

### Devices & System

Shows device, protocol, service and database status in one consolidated view. Configured thresholds and other operating parameters are shown under Settings. The former Expert view remains removed because its operational data is available here and under Settings.

### GQ Radiation World Map

Uploads are optional and disabled by default. When `gmcmap_enabled` is false, the view is also hidden from the sidebar. When enabled, the view contains only external upload status, queue and history functions; local sites and events remain in their own view.

The persistent queue retries temporary failures and prevents duplicate publication. The app sends the radon value and GQ identifiers required by the configured protocol. Public location settings are managed in the GQ account; the app does not transmit its Home Assistant coordinates through this feature.

### History

History has independent filters and does not overwrite the selected Overview context. The CSV export uses the current History filters and includes all matching records, not only rows visible in the table.

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

### Privacy and location display

- `location_display_mode`: `full`, `reduced` or `hidden`

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

### Overview shows unexpected values

Check the selected device, site and campaign in the Overview context bar, then press Apply. The selected count is shown before the total database count. History has separate filters and does not change the Overview selection.

### Radon traffic light is marked provisional

The selected records do not yet provide a complete 24-hour assessment with the configured minimum coverage. The latest completed hour is therefore used temporarily. The basis line shows the available coverage.

### Location card is absent or less precise

Review `location_display_mode`. In `hidden` mode the card is intentionally omitted; `reduced` mode uses the Home Assistant location name and rounds coordinates to two decimals. Home Assistant may not expose a postal address, in which case the location name is used.

### GQ Radiation World Map is absent from the sidebar

This is expected when `gmcmap_enabled` is false. Enable the function in the app options only when external publication is intended.

### Device not connected

Check USB mapping, permissions, configured port and whether another process has opened the serial device. Review Devices & System and the app log.

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

Version 5.2.0 includes tests for filter-coherent Overview statistics, context query parameters, 24-hour traffic-light assessment and provisional fallback, precise/reduced/hidden location display, coordinate units, event markers, separation of local sites from the optional World Map, collapsed advanced Analysis, release assets, API routes, destructive workflows, token redaction, USB reconnect state, database migrations, damaged restores, three years of hourly report data, responsive layouts, all eight interface languages, keyboard operation and 200% text scaling.

Real-device and real-Home-Assistant field testing remains necessary for USB hardware variations, Home Assistant upgrades and Recorder backends.
