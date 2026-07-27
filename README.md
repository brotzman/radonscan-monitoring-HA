# Radon Monitoring Home Assistant Repository 5.5.0

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.0 is a stability and maintainability release. The Rooms & events workflow is now guided in two steps, validation appears directly at the affected field, measurement assignments are visible, duplicate submissions are idempotent, and room saving has a URL fallback in addition to regular JSON and chunked request handling for Home Assistant Ingress.

Devices & System now includes a non-destructive System self-test for database integrity, room persistence, report-directory access and the device, MQTT and Home Assistant connections. The room/event browser controller and system diagnostics were moved into separate modules, and a compatibility matrix documents what is covered automatically and what still requires a real installation.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
