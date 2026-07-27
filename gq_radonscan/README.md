# Radon Monitoring 5.5.0

Radon Monitoring is a local Home Assistant app for read-only monitoring of compatible GQ RadonScan devices. It imports completed hourly values, stores raw and converted measurements in SQLite, publishes Home Assistant entities through MQTT, provides scientific time-series analysis, generates PDF reports and can optionally upload measurements to the GQ Radiation World Map.

## Main capabilities

- read-only SPIR device communication
- completed hourly values with raw CPH and the factor stored for each record
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

## Version 5.5.0

Version 5.5.0 combines workflow hardening with a clearer **Analysis** view. The statistical page is now reordered into concentration level, thresholds and exceedances, distribution and variability, development and period comparison, data quality and event impact. The separate **Time patterns** tile was removed from Advanced statistics. New rolling 24-hour, 7-day and 30-day means, additional percentiles, variability metrics, previous-period comparison and exploratory event-impact estimates complement the existing scientific diagnostics.

**Rooms & events** remains explicitly ordered: first create or edit a room, then assign a device and measurement period. The second step remains disabled until a room exists. Saved assignments are shown below the room list so the user can verify room, device, period and sample count.

Validation messages are displayed directly below the affected field. Room names are normalised and length-checked, decimal commas are accepted for measurement height, repeated submissions update the same room, and renaming a room to an existing name is rejected. A successful save is accepted only when the server returns the stored record identifier.

Room requests use the JSON body as the canonical source. For Home Assistant Ingress variants that unexpectedly forward an empty body, the browser also adds encoded fallback headers and query parameters. The server accepts regular JSON, URL-encoded forms and bounded chunked transfer encoding. Location and building data are never duplicated: place/address and building remain read-only values from Home Assistant, while only room and measurement height are stored locally.

**Devices & System** now contains a non-destructive System self-test. It checks the web API, SQLite integrity, a real room insert/read operation rolled back inside a savepoint, write access to the report directory, and the current RadonScan, MQTT and Home Assistant connections. Connection outages are reported as warnings; persistence or integrity failures are errors.

The feature controllers are less monolithic: `rooms-events.js` owns the room, assignment and event workflow; `system-diagnostics.js` owns the self-test display; `room_metadata.py` centralises request normalisation and validation; and `diagnostics.py` executes operational checks. The compatibility matrix in `maintainer/COMPATIBILITY.md` records automated coverage separately from real-installation validation.

The existing coherent Overview, 24-hour Radon traffic light, location privacy modes, event markers, visible data gaps, collapsed scientific Analysis and optional World Map behaviour remain unchanged.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Version 5.5.0 does not introduce a database-schema change. Existing 4.x, 5.0.0, 5.1.0, 5.2.0 and 5.3.0 databases open in place.

Before upgrading:

1. Create a Home Assistant backup and, where appropriate, an app database backup.
2. Stop the app before replacing a local repository package.
3. Start the updated app and confirm that the sidebar or Help view reports version 5.5.0.
4. Reopen the Ingress panel if an old iframe remains visible.
5. Review `location_display_mode` if the Overview is shown in screenshots or shared displays.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, sufficient measurement duration or qualified medical, building-physics or regulatory interpretation.

Home Assistant's public configuration normally supplies a location name, coordinates, elevation, country and time zone, but not every release supplies a structured postal address. Radon Monitoring never derives an address through an external geocoding service.

Recorder purge verification checks recent Home Assistant History API results. It cannot prove immediate physical compaction of every Recorder backend and does not imply that separately retained long-term statistics have been removed.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
