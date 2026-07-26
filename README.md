# Radon Monitoring Home Assistant Repository 5.0.0

This repository contains the `gq_radonscan` Home Assistant app for local, read-only monitoring of compatible GQ RadonScan devices.

Version 5.0.0 streamlines the Expert view by removing the Block checksums and Runtime status cards together with their unused frontend handlers. Release metadata, tests and the German and English manuals were updated accordingly.

## Test from the repository root

```bash
python3 -m pytest
```

The test configuration automatically adds the app library path and discovers the complete app test suite.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
