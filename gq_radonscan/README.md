# Radon Monitoring 5.0.0

Radon Monitoring is a local Home Assistant app for read-only monitoring of compatible GQ RadonScan devices. It imports completed hourly values, stores raw and converted measurements in SQLite, publishes Home Assistant entities through MQTT, provides scientific time-series analysis, generates PDF reports and can optionally upload measurements to the GQ Radiation World Map.

## Main capabilities

- read-only SPIR device communication
- completed hourly values with raw CPH and the factor used for each record
- Overview, Analysis and Expert views
- real 24-hour, 7-day and 30-day windows with duration and completeness checks
- robust descriptive statistics, confidence intervals, trend diagnostics and threshold-event analysis
- measurement sites, sessions, events, calibration records and factor history
- scientific PDF reports with method metadata and data checksum
- optional GQ Radiation World Map queue with retry and duplicate protection
- local backup, validated restore and complete local database reset
- optional complete Home Assistant Recorder purge for RadonScan entities, plus verification through the History API
- interface and Home Assistant option translations in German, English, Spanish, French, Croatian, Italian, Dutch and Polish

## Version 5.0.0

This release simplifies the Expert view. The Block checksums and Runtime status cards, their clipboard action and their frontend rendering code have been removed. Technical device, protocol, measurement and database information remains visible, while the downloadable diagnostics continue to provide the detailed diagnostic payload when required.

Automated checks cover the real web server, database reset, Recorder purge and verification, USB reconnect state, token redaction, three years of hourly report data, all main views at multiple viewport sizes, all eight languages, 200% text scaling and keyboard operation.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Version 5.0.0 does not introduce a database-schema change. Existing 4.x databases open in place.

Before upgrading:

1. Create a Home Assistant backup and, where appropriate, an app database backup.
2. Stop the app before replacing a local repository package.
3. Start the updated app and confirm that the sidebar or Help view reports version 5.0.0.
4. Reopen the Ingress panel if an old iframe remains visible.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, sufficient measurement duration or qualified medical, building-physics or regulatory interpretation.

Recorder purge verification checks recent Home Assistant History API results. It cannot prove immediate physical compaction of every Recorder backend and does not imply that separately retained long-term statistics have been removed.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
