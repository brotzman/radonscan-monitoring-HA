# Radon Monitoring 4.6.0

Radon Monitoring is a local Home Assistant app for read-only monitoring of GQ RadonScan devices. It imports completed hourly values, stores raw and converted measurements in SQLite, publishes Home Assistant entities through MQTT, provides statistical analysis, generates scientific PDF reports and can optionally upload to the GQ Radiation World Map.

## Main capabilities

- read-only SPIR device communication
- completed hourly values with raw CPH and stored conversion factor
- Overview, Analysis and Expert views
- real 24-hour, 7-day and 30-day windows with completeness checks
- robust descriptive and time-series statistics
- moving-block-bootstrap confidence intervals and effective sample size
- measurement sites, sessions, events and calibration history
- scientific PDF reports with method metadata and data checksum
- optional GQ Radiation World Map queue with retry and duplicate protection
- local backup, restore and complete database reset
- optional complete Home Assistant Recorder purge for RadonScan entities
- German, English, Spanish, French, Croatian, Italian, Dutch and Polish interface files

## 4.6.0 focus

Version 4.6.0 is a consolidation release. It updates the manuals, cleans the changelog, separates reusable frontend infrastructure, improves the statistical information hierarchy and adds release-integrity and migration regression tests. The database schema is unchanged from 4.5.0.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Existing 4.x data is migrated or opened in place. Create a backup before upgrading and verify the displayed version after reopening the Home Assistant Ingress panel.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, adequate measurement duration or qualified legal/medical interpretation.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
