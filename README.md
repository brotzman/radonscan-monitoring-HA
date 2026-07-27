# Radon Monitoring Home Assistant Repository 5.5.9

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.9 corrects the relationship between device-read time and measurement time. New hourly records are timestamped from the previous stored hour index, so a delayed poll no longer appears as the completion time of the measurement. Existing irregular timestamps are repaired once during the upgrade.

A newly appearing zero-count hour is now confirmed by a second successful device read before it is stored. Confirmed zeroes remain valid measurements and continue to contribute to the 24-hour and 7-day averages. The interface separately displays the last device read, the last completed measurement and the time for which the hour index has remained unchanged.

The radon-only GQ World Map upload and fixed serial-port selection from earlier 5.5.x releases remain in place. `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` is used exclusively unless `serial_port` is explicitly set to `auto`, and unrelated Zigbee, Z-Wave and console adapters are skipped during automatic discovery.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
