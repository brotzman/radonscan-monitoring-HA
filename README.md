# Radon Monitoring Home Assistant Repository 5.5.2

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.2 corrects the GQ Radiation World Map integration for pure RadonScan measurements. Uploads now use the dedicated `rdlog.asp` radon endpoint and submit only `AID`, `GID` and `pCi`.

The former generic request included `CPM=0`. GMCMap interpreted that placeholder as a real radioactivity measurement and displayed an additional zero value on the radioactivity map. Version 5.5.2 no longer sends `CPM`, `ACPM` or `uSV`, so new uploads are classified as radon-only measurements.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
