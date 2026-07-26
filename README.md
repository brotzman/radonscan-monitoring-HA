# Radon Monitoring Home Assistant Repository 5.3.0

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.3.0 simplifies the location model. The Overview now selects only device and campaign; the current room is determined automatically from the time-based room assignment and is shown beneath the Home Assistant location together with the measurement height. Place/address, building or location name, coordinates, elevation, country and time zone come from Home Assistant's local Core configuration. Only room and measurement height are entered manually in Radon Monitoring.

The former Measurement sites area is now **Rooms & events**. It manages rooms, measurement campaigns, time-based assignments and documented events without duplicating Home Assistant location or building data. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`. No external geocoding service is used.

The 24-hour Radon traffic light, 24-hour peak, event markers, visible data gaps, privacy modes and collapsible scientific Analysis introduced in the 5.x interface remain available.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
