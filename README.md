# Radon Monitoring Home Assistant Repository 5.5.1

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.1 is a **UI polishing release**. It focuses on the mobile presentation of Overview, Analysis and Data statistics by using more compact statistic cards, denser but still readable spacing, and improved wrapping of labels, helper texts and values in narrow Home Assistant WebViews.

The release keeps the existing analysis structure and functionality from 5.5.0, but presents them more efficiently on smaller screens. Two-column card layouts are preserved longer on mobile before collapsing to a single column on very narrow displays, and statistical fact grids are tuned for clearer label/value stacking.

Place/address and building continue to come directly from Home Assistant. Only room and measurement height are maintained locally. Coordinates include degree units and cardinal directions, for example `51,60176° N, 7,45410° E`; no external geocoding service is used.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
