# Radon Monitoring 5.3.0

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
- scientific PDF reports with method metadata and data checksum
- optional GQ Radiation World Map queue with retry and duplicate protection; hidden from navigation when disabled
- local backup, validated restore and complete local database reset
- optional complete Home Assistant Recorder purge for RadonScan entities, plus verification through the History API
- interface and Home Assistant option translations in German, English, Spanish, French, Croatian, Italian, Dutch and Polish

## Version 5.3.0

The Overview context contains only **device** and **campaign**. The current room is resolved automatically from the time-based room assignment, so there is no separate room or measurement-site selector on the Overview. The current value, period statistics, sample count, peak and chart use the same resolved context. Beneath the Home Assistant location card, the interface shows only the room and, when available, the measurement height.

Place or address, building/location name, coordinates, elevation, country and time zone are read from Home Assistant's local Core configuration. They are displayed as read-only source data in **Local metadata > Rooms & events** and cannot be duplicated or changed in Radon Monitoring. Only the room and measurement height are maintained manually. Existing temporal assignments, campaigns and events continue to remain local.

The Radon traffic light uses the **24-hour mean** once that period has sufficient duration and data coverage. Until then it falls back to the latest completed hourly value and marks the assessment as **provisional**. Its basis and coverage are shown below the signal. The former overall-average tile remains replaced by the maximum observed value within the latest 24-hour window, including time and coverage.

Documented events such as ventilation, interventions or device changes appear as markers in the Overview and Analysis charts. Data gaps remain visible as breaks rather than being connected by a misleading line. Analysis opens with a readable result sentence; extended scientific quality, uncertainty, autocorrelation and distribution details are collapsed by default.

The Home Assistant location card supports three modes through `location_display_mode`:

- `full`: locally supplied address or location name and precise coordinates
- `reduced`: location name and coordinates rounded to two decimals
- `hidden`: no location card on the Overview

Coordinates include the angular unit and direction, for example `51,60176° N, 7,45410° E`. Radon Monitoring does not reverse-geocode or send these values to an external geocoding service.

## Upgrade notes

The slug `gq_radonscan`, data path, SQLite filename, MQTT identifiers and entity unique IDs remain unchanged. Version 5.3.0 does not introduce a database-schema change. Existing 4.x, 5.0.0 and 5.1.0 databases open in place.

Before upgrading:

1. Create a Home Assistant backup and, where appropriate, an app database backup.
2. Stop the app before replacing a local repository package.
3. Start the updated app and confirm that the sidebar or Help view reports version 5.3.0.
4. Reopen the Ingress panel if an old iframe remains visible.
5. Review `location_display_mode` if the Overview is shown in screenshots or shared displays.

## Important limitations

This is a community implementation. The bundled SPIR protocol reference is not an official GQ specification. Statistical analysis cannot replace documented calibration, suitable placement, sufficient measurement duration or qualified medical, building-physics or regulatory interpretation.

Home Assistant's public configuration normally supplies a location name, coordinates, elevation, country and time zone, but not every release supplies a structured postal address. Radon Monitoring never derives an address through an external geocoding service.

Recorder purge verification checks recent Home Assistant History API results. It cannot prove immediate physical compaction of every Recorder backend and does not imply that separately retained long-term statistics have been removed.

See `DOCS.md`, the built-in user manual and `CHANGELOG.md` for details.
