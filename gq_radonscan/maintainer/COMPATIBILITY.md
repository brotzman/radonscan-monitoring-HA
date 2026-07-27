# Compatibility matrix - Radon Monitoring 5.5.2

This matrix distinguishes automated contract coverage from checks that require a real Home Assistant installation and physical RadonScan hardware. A green automated test does not imply that every Home Assistant release, browser WebView or USB adapter has been field-tested.

| Component | Compatibility target | Automated coverage | Field validation before broad rollout |
|---|---|---|---|
| Home Assistant Ingress | Relative routes, cached assets, JSON, URL-encoded and chunked POST forwarding | Real local HTTP server tests, empty-body query fallback and browser workflow tests | Open the add-on through the Home Assistant web UI and mobile app; create, edit and assign a room |
| Home Assistant Core API | `/api/config`, events, states and History API | Mocked Core responses and unreachable-Core behaviour | Confirm location metadata, version, Recorder purge and history verification on the target installation |
| Browser | Current Chromium-compatible desktop and mobile WebViews | Chromium at 320, 390, 768 and 1440 px; keyboard and 200% text tests | Safari/iOS Home Assistant app and any deployment-specific kiosk browser |
| GQ RadonScan | Read-only GETVER/SPIR communication | Decoder fixtures, import and reconnect state tests | Physical USB device, supported firmware, `/dev/serial/by-id` path and reconnect |
| MQTT | Standard broker connection and Home Assistant discovery | Runtime state and publication tests | Broker outage/recovery and retained discovery on the target broker |
| SQLite | Existing schema version 8 databases | Migration, integrity, backup/restore and non-destructive room round-trip tests | Upgrade a copy of the production database and verify historical reports |
| CPU architecture | Home Assistant add-on architectures declared in `config.yaml` | Python portability tests in the build environment | Build and start each architecture image offered by the repository |

## Release recording

For every release, record the Home Assistant version, installation type, browser/WebView, architecture, RadonScan firmware, USB identifier and result of the built-in System self-test. Do not mark an environment as field-tested until the complete room workflow and at least one new completed hourly measurement have been verified.

## GQ Radiation World Map

- Automated: the outbound RadonScan request targets `rdlog.asp` and contains only `AID`, `GID` and `pCi`.
- Field verification still required: confirm with the configured GMCMap account that new values appear exclusively in the radon view. Previously uploaded 0 CPM records are external data and are not removed by this release.
