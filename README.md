# Radon Monitoring Home Assistant Repository 5.5.5

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.5 reduces Home Assistant MQTT discovery to exactly three Radon entities: the completed hourly value, the 24-hour mean and the 7-day mean. All three always use `Bq/m³`, regardless of the display unit selected inside the app. Obsolete discovery entries from previous releases are removed automatically after the first successful MQTT connection.

The radon-only GQ World Map upload and fixed serial-port selection from earlier 5.5.x releases remain in place. `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` is used exclusively unless `serial_port` is explicitly set to `auto`, and unrelated Zigbee, Z-Wave and console adapters are skipped during automatic discovery.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
