# Radon Monitoring Home Assistant Repository 5.5.14

This repository contains the Home Assistant app **Radon Monitoring** for compatible GQ RadonScan devices.

Version 5.5.14 fixes long-running read-only SPIR imports when the visible 14-byte time-record window no longer begins with the original `t=0` marker. A continuous, hour-aligned non-zero history window is now accepted and paired with the matching raw CPH values instead of being rejected with `first time record is not t=0`.

Fresh histories keep the established `t=0` marker behaviour unchanged. Strict 3600-second continuity, block-size checks, raw-value plausibility checks and read-only transport remain enforced. No database-schema change is introduced.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md`, `gq_radonscan/maintainer/COMPATIBILITY.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
