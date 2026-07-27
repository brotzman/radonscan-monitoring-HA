# Radon Monitoring 5.5.11

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

## Version 5.5.11

Version 5.5.11 gives the **Hourly measurements** view a clearer visual hierarchy. The latest row is highlighted, calendar-day groups are separated, and alternating backgrounds make long histories easier to scan. Each Radon value now includes a proportional concentration bar, so values such as 1.54, 3.08, 6.16 and 20.02 Bq/m³ are visually distinct even though they all remain far below the configured warning threshold.

The table header now includes compact summaries for measurement count, mean and maximum. Raw CPH, room and campaign use restrained badges, while device model and serial number are separated typographically. On narrow screens the table becomes a stack of responsive measurement cards instead of requiring horizontal scrolling.

This release changes presentation only. Bq/m³ remains visible with two decimal places, pCi/L remains at three decimal places, and stored measurement precision, calculations, MQTT entities, APIs and the database schema are unchanged.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Version 5.5.11 does not introduce a database-schema change. Existing 4.x, 5.0.0, 5.1.0, 5.2.0 and 5.3.0 databases open in place.

Before upgrading:

1. Create a Home Assistant backup and, where appropriate, an app database backup.
2. Stop the app before replacing a local repository package.
3. Start the updated app and confirm that the sidebar or Help view reports version 5.5.11.
4. Reopen the Ingress panel if an old iframe remains visible.
5. Review `location_display_mode` if the Overview is shown in screenshots or shared displays.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, sufficient measurement duration or qualified medical, building-physics or regulatory interpretation.

Home Assistant's public configuration normally supplies a location name, coordinates, elevation, country and time zone, but not every release supplies a structured postal address. Radon Monitoring never derives an address through an external geocoding service.

Recorder purge verification checks recent Home Assistant History API results. It cannot prove immediate physical compaction of every Recorder backend and does not imply that separately retained long-term statistics have been removed.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
