# Radon Monitoring Home Assistant Repository 5.5.3

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.3 stabilises serial-device selection. The configured RadonScan path `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` is used exclusively instead of probing every USB, Zigbee and console adapter on the Home Assistant host.

Automatic discovery remains available when `serial_port` is explicitly set to `auto`; it now skips recognisable Sonoff, ITEAD, Zigbee, Z-Wave and `/dev/ttyAMA*` devices and de-duplicates aliases that point to the same physical port. The interface reports whether a port is busy, missing, silent or connected to the wrong device type.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
