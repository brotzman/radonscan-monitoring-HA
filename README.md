# Radon Monitoring Home Assistant Repository 5.5.4

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.4 corrects the GQ World Map upload target. Radon values are now submitted to GMCMap's documented public `log2.asp` endpoint using only `AID`, `GID` and `pCi`; no `CPM`, `ACPM` or `uSV` field is sent.

The fixed serial-port selection from 5.5.3 remains in place. `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` is used exclusively unless `serial_port` is explicitly set to `auto`, and unrelated Zigbee, Z-Wave and console adapters are skipped during automatic discovery.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
