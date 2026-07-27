# Radon Monitoring Home Assistant Repository 5.5.13

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.13 fixes the blank **Weekly heatmap** in Analysis. The heatmap now renders reliably even when the Analysis response arrives before the initial application settings, and it can reconstruct the full 7 x 24 grid from the selected records if the precomputed API grid is unavailable.

All weekday and hourly cells are always visible. Missing combinations remain hatched, while available measurements are coloured according to the configured warning and danger thresholds once the application state has loaded.

All stored measurements, calculations, MQTT entities, upload logic, API routes and database structures remain unchanged.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
