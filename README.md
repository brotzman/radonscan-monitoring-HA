# Radon Monitoring Home Assistant Repository 4.9.0

This repository contains the `gq_radonscan` Home Assistant app for local, read-only monitoring of compatible GQ RadonScan devices.

Version 4.9.0 focuses on reliability and verification: modular destructive-data workflows, token redaction, Recorder purge verification, multi-year report performance, native option translations, browser end-to-end tests and updated German and English manuals.

## Test from the repository root

```bash
python3 -m pytest
```

The test configuration automatically adds the app library path and discovers the complete app test suite.

See `gq_radonscan/README.md`, `gq_radonscan/DOCS.md` and `gq_radonscan/CHANGELOG.md` for installation, operation and release details.
