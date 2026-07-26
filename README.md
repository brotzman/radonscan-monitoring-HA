# Radon Monitoring Home Assistant Repository 5.2.0

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.2.0 makes the Overview filter-aware and easier to interpret: device, measurement site and campaign can be selected directly; the Radon traffic light uses the 24-hour mean when available and labels an hourly fallback as provisional; the former overall mean card is replaced by the 24-hour peak; documented events are marked in time-series charts; and the scientific Analysis details start collapsed behind a plain-language summary.

Measurement sites and events now have their own navigation view. The optional GQ Radiation World Map view is hidden when upload is disabled. Home Assistant location data can be shown in full, reduced or hidden form. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`, and no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
