# Radon Monitoring Home Assistant Repository 5.3.2

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.3.2 fixes room saving through Home Assistant Ingress when the proxy forwards POST data with chunked transfer encoding or unexpectedly omits the request body. The server now decodes chunked requests correctly and the browser supplies an encoded fallback header. The simplified location model remains unchanged: place/address and building come from Home Assistant, while only room and measurement height are entered manually.

The former Measurement sites area is now **Rooms & events**. It manages rooms, measurement campaigns, time-based assignments and documented events without duplicating Home Assistant location or building data. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`. No external geocoding service is used.

The 24-hour Radon traffic light, 24-hour peak, event markers, visible data gaps, privacy modes and collapsible scientific Analysis introduced in the 5.x interface remain available.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
