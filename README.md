# Radon Monitoring Home Assistant Repository 5.5.12

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.12 simplifies long list views. The hourly measurement history and the GQ World Map upload history now show exactly ten entries per page with clear previous/next arrow controls and a visible page range.

The separate administration-log panel has been removed from Data management. Operational audit records remain stored internally for traceability, but the raw JSON table is no longer presented in the normal user interface.

All stored measurements, calculations, MQTT entities, upload logic, API routes and database structures remain unchanged.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
