# Radon Monitoring 5.5.14

Radon Monitoring is a local Home Assistant app for read-only monitoring of compatible GQ RadonScan devices. It imports completed hourly values, stores raw and converted measurements in SQLite, publishes Home Assistant entities through MQTT, provides scientific time-series analysis, generates PDF reports and can optionally upload measurements to the GQ Radiation World Map.

## Main capabilities

- read-only SPIR device communication
- completed hourly values with raw CPH and the factor stored for each record
- exactly three Home Assistant MQTT entities in Bq/m³: hourly Radon value, 24-hour mean and 7-day mean
- coherent Overview for device and campaign with automatic room resolution
- Radon traffic light based primarily on the 24-hour mean, with an explicitly provisional hourly fallback
- Home Assistant location summary with configurable privacy level and no external geocoding
- coordinate display with degree units and cardinal directions
- real 24-hour, 7-day and 30-day windows with duration and completeness checks
- 24-hour peak, event markers and visible time-series gaps
- plain-language Analysis summary plus collapsible advanced scientific diagnostics
- robust descriptive statistics, confidence intervals, trend diagnostics and threshold-event analysis
- dedicated Rooms & events view; only room and measurement height are entered manually
- guided room/device/time assignment workflow with visible assignment history and inline validation
- non-destructive System self-test with actionable check results
- scientific PDF reports with method metadata and data checksum
- optional GQ Radiation World Map queue with retry and duplicate protection; hidden from navigation when disabled
- local backup, validated restore and complete local database reset
- optional complete Home Assistant Recorder purge for RadonScan entities, plus verification through the History API
- interface and Home Assistant option translations in German, English, Spanish, French, Croatian, Italian, Dutch and Polish

## Version 5.5.14

Version 5.5.14 fixes a long-running SPIR history compatibility failure seen after the device's visible 14-byte time-record window no longer starts with the original `t=0` marker. Earlier releases treated any non-zero first record as corrupt and repeatedly reported `first time record is not t=0`.

The decoder now preserves the original marker semantics for fresh histories and additionally accepts a non-zero first hour when the complete visible time-record sequence is still strictly hour-aligned and advances by exactly 3600 seconds. In that rolling-window state every visible time record is paired with one raw CPH value. Alignment, 4096-byte block-size, conversion-factor and implausible-CPH checks remain unchanged.

The decoder diagnostics now expose whether the origin marker is present and the first visible hour index. The database schema, stored measurements, MQTT identifiers, World Map format and read-only device transport are unchanged.

## Version 5.5.13

Version 5.5.13 fixes a load-order error that could leave the **Weekly heatmap** panel empty. When Analysis was opened before the initial application state had finished loading, the renderer tried to read threshold settings from an unavailable state object and stopped before creating the grid.

The heatmap now uses safe temporary thresholds, re-renders when the configured settings become available and always creates a complete grid of seven weekdays by 24 hours. If the API heatmap is absent or malformed, the browser reconstructs the hourly weekday means from the selected analysis records using the configured analysis time zone.

Cells without sufficient data remain visibly hatched. Existing measurements, statistical calculations, ten-entry history pagination, MQTT entities, World Map uploads, APIs and the database schema remain unchanged.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Version 5.5.14 does not introduce a database-schema change. Existing 4.x, 5.0.0, 5.1.0, 5.2.0 and 5.3.0 databases open in place.

Before upgrading:

1. Create a Home Assistant backup and, where appropriate, an app database backup.
2. Stop the app before replacing a local repository package.
3. Start the updated app and confirm that the sidebar or Help view reports version 5.5.14.
4. Reopen the Ingress panel if an old iframe remains visible.
5. Review `location_display_mode` if the Overview is shown in screenshots or shared displays.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, sufficient measurement duration or qualified medical, building-physics or regulatory interpretation.

Home Assistant's public configuration normally supplies a location name, coordinates, elevation, country and time zone, but not every release supplies a structured postal address. Radon Monitoring never derives an address through an external geocoding service.

Recorder purge verification checks recent Home Assistant History API results. It cannot prove immediate physical compaction of every Recorder backend and does not imply that separately retained long-term statistics have been removed.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
