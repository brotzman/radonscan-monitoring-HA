# Radon Monitoring Home Assistant Apps

Repository for **Radon Monitoring 4.3.7**, a local Home Assistant App for GQ RadonScan devices.

The app reads completed hourly values from the reverse-engineered, read-only SPIR history of a compatible GQ RadonScan, stores them in SQLite and publishes the established MQTT Discovery entities. Version 4.1 adds a complete local analysis and documentation workspace while preserving the existing app slug, database path, MQTT topic prefix and entity identifiers.

## Main functions

- read-only USB/SPIR acquisition of completed hourly values
- true time-window averages with explicit handling of incomplete periods
- overview, analysis and expert views with explicit multi-device filtering
- statistical evaluation, data-quality metrics and visible data gaps
- optional manual and automatic upload to the GQ Radiation World Map
- local measurement-site assignment without floor-plan images
- measurement sessions and event annotations
- compact and detailed scientific PDF reports
- CSV, diagnostics and complete ZIP backups
- controlled deletion by period, device or campaign and restoration of local data
- selective Home Assistant Recorder purge for detected Radon Monitoring entities
- MQTT Discovery compatibility with version 3 installations

## Installation

1. Make the repository available to Home Assistant, or copy `gq_radonscan/` into the local apps directory.
2. Reload the Home Assistant App Store.
3. Install **Radon Monitoring**.
4. Connect the GQ RadonScan through USB and provide the MQTT service.
5. Start the app and open the **Radon Monitoring** panel.

The visible name changed, but the internal slug remains `gq_radonscan` to permit an in-place upgrade.

## Safety

Device access remains strictly read-only. The implementation sends GET and SPIR read requests and does not send SET, WRITE, ERASE or RESET commands. Statistics and reports are orientation aids and are not a substitute for medical, regulatory or professional building assessment.


Current release: **Radon Monitoring 4.3.7**.


### Home Assistant Recorder-Verlauf löschen

Die Aktion `recorder.purge_entities` ist in aktuellen Home-Assistant-Versionen administratorgeschützt. Falls der Supervisor-Token abgewiesen wird, in Home Assistant unter **Profil → Sicherheit → Langlebige Zugriffstoken** einen Token eines Administrators erstellen und in der App-Option `homeassistant_access_token` hinterlegen. Der Token wird nicht in der Weboberfläche oder in Diagnoseausgaben angezeigt.
