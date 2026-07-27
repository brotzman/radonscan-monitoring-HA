# Radon Monitoring 5.5.5 - App documentation

## Purpose

Radon Monitoring reads completed hourly records from compatible GQ RadonScan devices using read-only SPIR commands. It stores measurements locally, exposes selected values to Home Assistant through MQTT and provides analysis, reporting and controlled data-management workflows.

The app is an orientation and documentation tool. It does not turn a consumer monitor into a certified regulatory measurement system.

## First start

1. Connect the RadonScan by USB.
2. Ensure an MQTT broker is available to Home Assistant.
3. Use the fixed path `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`. Set `serial_port` to `auto` only when automatic discovery is deliberately required.
4. Start the app and open its Ingress panel.
5. Check the connection state, firmware, current configured factor and first completed hourly value.

Only completed hours are imported. A newly connected device may therefore remain without a current value until a completed record is available.

## Home Assistant entities in 5.5.5

MQTT discovery exposes exactly three sensor entities and all of them use `Bq/m³`:

- completed hourly Radon value
- 24-hour mean
- 7-day mean

The web-interface preference for `pCi/L` affects only the app display and reports; it does not change the Home Assistant entity units. The 30-day mean, raw CPH, hour index, last update, sample count and connectivity binary sensor are no longer published as Home Assistant entities.

During the first successful MQTT connection after an upgrade, retained empty discovery payloads are published for those obsolete entity topics. Home Assistant should therefore remove them automatically. The three retained sensors keep their existing unique IDs so their entity IDs and history remain associated with the same sensors wherever Home Assistant permits the unit transition.

## Fixed serial-port selection retained from 5.5.3

A configured `serial_port` is exclusive. Radon Monitoring opens only that path and does not append every serial interface found on the host. This prevents accidental probes of Sonoff/ITEAD Zigbee adapters, other USB serial devices and internal `/dev/ttyAMA*` console ports.

The default stable path for this installation is:

```text
/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
```

When an older Home Assistant options file still contains an empty value, the app adopts this path automatically. The explicit value `auto` always keeps automatic discovery enabled.

Automatic discovery prefers `/dev/serial/by-id/` aliases, de-duplicates aliases by their resolved device path and skips names that clearly identify Sonoff, ITEAD, Zigbee, Z-Wave, ConBee, SkyConnect or Ember adapters. `/dev/ttyAMA*` is never scanned automatically but can still be used when configured explicitly.

The connection runtime and Devices & System view distinguish `port_busy`, `port_not_found`, `permission_denied`, `no_response`, `wrong_device`, `read_error`, `no_ports` and `not_detected`. The checked port remains visible even when the device is disconnected. The service start log reads the real application version.

## Views

### Overview

The context bar selects a **device** and **campaign**. The most recently or currently assigned room is resolved automatically from the time-based room assignment; there is no separate room or measurement-site selector on the Overview. Applying the context reloads the latest measurement, 24-hour, 7-day and 30-day summaries, selected sample count, 24-hour peak and chart from one coherent device/campaign/room record set.

The Radon traffic light uses the 24-hour mean when the period has sufficient duration and coverage. Before that condition is met, it uses the latest completed hourly value and labels the result as provisional. The exact assessment basis, data coverage and configured warning/danger thresholds are shown with the signal.

The fourth overview metric is the maximum observed value in the latest 24-hour window, with measurement time and coverage. Documented events are drawn as vertical markers in the chart. Gaps longer than 90 minutes split the line so missing data is not visually interpolated.

The Home Assistant location card reads only local Core configuration values. In full mode it shows the locally supplied address, or the configured location name when no address is exposed, plus coordinates, elevation, country and time zone. Coordinates include degrees and cardinal directions, for example `51,60176° N, 7,45410° E`. Directly below the location information, the card shows only the automatically resolved **room** and optional **measurement height**. No reverse geocoding is performed and no location values are sent to an external geocoding service.

`location_display_mode` controls disclosure:

- `full`: address/location name and precise coordinates
- `reduced`: location name and coordinates rounded to two decimals
- `hidden`: card, including room and measurement height, omitted from the Overview

### Analysis

Analysis starts with a plain-language summary of trend direction, warning-threshold share, danger-threshold share and data coverage. Basic statistics remain immediately visible. Scientific quality, counting uncertainty, effective sample size, confidence intervals, autocorrelation, distribution diagnostics and sensitivity results are grouped under a collapsed advanced section.

The analysis time series includes documented events and visible gaps. Missing values are not imputed and flagged observations are not silently deleted. Statistical significance does not establish causality; event notes and measurement conditions still require professional interpretation.

### Rooms & events

This dedicated Local metadata view manages rooms, measurement campaigns, time-based device-to-room assignments and event documentation. Place/address and building/location name are shown as read-only values obtained directly from Home Assistant's general settings. They are not entered or stored a second time in the form.

Only **room** and **measurement height** are added manually. The form validates values inline and confirms the saved database record before enabling the assignment step. Existing time-based assignments are listed below the rooms so incorrect room/device periods can be noticed immediately. Ventilation, interventions, construction work, outages and device moves can be documented without altering original measurement values. Existing database identifiers and assignment records remain compatible with older releases.

### Devices & System

Shows device, protocol, service and database status in one consolidated view. The **System self-test** checks the web endpoint, database integrity, room persistence, report-directory access and the current RadonScan, MQTT and Home Assistant connections. A disconnected external service is a warning; a failed local integrity or persistence check is an error. Configured thresholds and other operating parameters are shown under Settings. The former Expert view remains removed because its operational data is available here and under Settings.

### GQ Radiation World Map

Uploads are optional and disabled by default. When `gmcmap_enabled` is false, the view is also hidden from the sidebar. When enabled, the view contains only external upload status, queue and history functions; local rooms, assignments and events remain in their own view.

The persistent queue retries temporary failures and prevents duplicate publication. RadonScan measurements use GMCMap's documented public `log2.asp` endpoint and submit only `AID`, `GID` and `pCi`. The application deliberately omits `CPM`, `ACPM` and `uSV`, so no artificial radioactivity value is generated.

Public location settings are managed in the GQ account; the app does not transmit its Home Assistant coordinates through this feature. Previously uploaded zero-valued radioactivity records remain on the external GMCMap service and cannot be deleted by the local application.

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

RadonScan uploads are radon-only and use `log2.asp` with `AID`, `GID` and `pCi`. No Geiger-counter fields are submitted.

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

Check the selected device and campaign in the Overview context bar, then press Apply. The room is taken automatically from the applicable time-based assignment and is shown below the Home Assistant location card. If no room appears, create a room with its measurement height under Rooms & events and assign the device for the required time range. History has separate filters and does not change the Overview context.

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

Version 5.5.5 includes request-level tests for radon-only GMCMap uploads and tests for filter-coherent Overview statistics, context query parameters, 24-hour traffic-light assessment and provisional fallback, precise/reduced/hidden location display, coordinate units, event markers, automatic room resolution, read-only Home Assistant place/building data, guided room creation and assignment, inline validation, query/header/chunked Ingress fallbacks, idempotent room saves, the non-destructive System self-test, visible assignment cards, separation of local rooms from the optional World Map, collapsed advanced Analysis, release assets, API routes, destructive workflows, token redaction, USB reconnect state, database migrations, damaged restores, three years of hourly report data, responsive layouts, all eight interface languages, keyboard operation and 200% text scaling.

Real-device and real-Home-Assistant field testing remains necessary for USB hardware variations, Home Assistant upgrades and Recorder backends.
