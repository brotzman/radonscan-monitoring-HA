# Radon Monitoring 4.4.7

A local Home Assistant App for completed hourly measurements from compatible GQ RadonScan devices.

## Highlights

- read-only USB access at 115200 baud, 8N1
- completed hourly CPH history from `0x1FC000`
- hour-index records from `0x1FE000`
- configurable conversion factor stored with every measurement
- migration-compatible SQLite database with campaign/reset detection
- MQTT Discovery using the established version-3 topics and unique IDs
- responsive Overview, Analysis and Expert views
- explicit multi-device filters for histories, sessions, analysis and reports
- true 24-hour, 7-day and 30-day windows with transparent coverage checks
- robust statistics, local-time profiles, trends, thresholds and data-gap analysis
- optional manual and automatic GQ Radiation World Map upload with queue, retries and duplicate protection
- measurement sites, sessions and event annotations without floor-plan uploads
- compact and detailed scientific PDF reports with SHA-256 checksums
- CSV, diagnostics JSON and complete ZIP backups
- controlled deletion, database restore, audit logging and selective Home Assistant Recorder purge

The app publishes a normal measurement only after the device has stored a completed hour. It does not invent minute-level values or fill missing hours.

The internal slug, database filename, MQTT topics and entity identifiers remain unchanged so existing installations can update in place.

## Documentation

- `DOCS.md`: installation, configuration, operation and maintenance reference
- built-in German and English user manuals: available from **Help** in the web interface
- localized protocol references: technical documentation of the confirmed read-only SPIR path

## Version 4.4.7

Version 4.4.7 updates the user documentation to the current application, adds new German and English PDF manuals, corrects obsolete version references and removes the Home Assistant experimental-stage marker. The app remains a community implementation and the device protocol is still not an official GQ specification.


### Home Assistant Recorder-Verlauf löschen

Die Aktion `recorder.purge_entities` ist in aktuellen Home-Assistant-Versionen administratorgeschützt. Falls der Supervisor-Token abgewiesen wird, in Home Assistant unter **Profil → Sicherheit → Langlebige Zugriffstoken** einen Token eines Administrators erstellen und in der App-Option `homeassistant_access_token` hinterlegen. Der Token wird nicht in der Weboberfläche oder in Diagnoseausgaben angezeigt.
