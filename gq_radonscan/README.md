# Radon Monitoring 5.1.0

Radon Monitoring is a local Home Assistant app for read-only monitoring of compatible GQ RadonScan devices. It imports completed hourly values, stores raw and converted measurements in SQLite, publishes Home Assistant entities through MQTT, provides scientific time-series analysis, generates PDF reports and can optionally upload measurements to the GQ Radiation World Map.

## Main capabilities

- read-only SPIR device communication
- completed hourly values with raw CPH and the factor used for each record
- Overview and Analysis views plus consolidated Devices & System status
- Home Assistant location summary using the local Core configuration
- Radon traffic light based on the configured warning and danger thresholds
- real 24-hour, 7-day and 30-day windows with duration and completeness checks
- robust descriptive statistics, confidence intervals, trend diagnostics and threshold-event analysis
- measurement sites, sessions, events, calibration records and factor history
- scientific PDF reports with method metadata and data checksum
- optional GQ Radiation World Map queue with retry and duplicate protection
- local backup, validated restore and complete local database reset
- optional complete Home Assistant Recorder purge for RadonScan entities, plus verification through the History API
- interface and Home Assistant option translations in German, English, Spanish, French, Croatian, Italian, Dutch and Polish

## Version 5.1.0

The Overview now contains a compact, responsive **Home Assistant location** card. It displays the location name or address provided by Home Assistant together with latitude, longitude, elevation, country and time zone. The data is read from Home Assistant through the local Core API; the app does not perform reverse geocoding and does not send the coordinates to an external geocoding service.

A new **Radon traffic light** classifies the latest completed hourly measurement as green, amber or red using the warning and danger thresholds configured in Settings. The former Expert view has been removed completely from the interface and sidebar because the required operational information is already available under Devices & System and Settings.

When a Home Assistant version does not expose a postal address, the configured Home Assistant location name is shown instead. Coordinates and the remaining available fields continue to be displayed.

Automated checks cover the local configuration mapping, Radon traffic-light thresholds, removal of the Expert view, the real web server, database reset, Recorder purge and verification, USB reconnect state, token redaction, three years of hourly report data, all remaining views at multiple viewport sizes, all eight languages, 200% text scaling and keyboard operation.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Version 5.1.0 does not introduce a database-schema change. Existing 4.x and 5.0.0 databases open in place.

Before upgrading:

1. Create a Home Assistant backup and, where appropriate, an app database backup.
2. Stop the app before replacing a local repository package.
3. Start the updated app and confirm that the sidebar or Help view reports version 5.1.0.
4. Reopen the Ingress panel if an old iframe remains visible.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, sufficient measurement duration or qualified medical, building-physics or regulatory interpretation.

Home Assistant's public configuration normally supplies a location name, coordinates, elevation, country and time zone, but not every release supplies a structured postal address. Radon Monitoring never derives an address through an external geocoding service.

Recorder purge verification checks recent Home Assistant History API results. It cannot prove immediate physical compaction of every Recorder backend and does not imply that separately retained long-term statistics have been removed.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
