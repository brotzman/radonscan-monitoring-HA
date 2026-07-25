# Radon Monitoring 4.6.0 - Technical and Operations Documentation

## 1. Purpose and scope

Radon Monitoring reads completed hourly values from compatible GQ RadonScan devices without sending write commands to the device. It stores the values locally, exposes Home Assistant entities, provides statistical analysis and produces reproducible reports.

## 2. Installation and upgrade

1. Install the app on a supported `amd64` or `aarch64` Home Assistant system.
2. Connect the RadonScan by USB and ensure no other program holds the serial port.
3. Provide the MQTT service and start the app.
4. Open the Ingress panel and verify device, MQTT and database status.
5. Before upgrades or destructive actions, create and download a backup.

The database remains at `/data/radonscan_v3.sqlite3`. The app slug and MQTT identities are preserved to avoid duplicate entities.

## 3. Interface levels

### Overview

Shows the latest completed hour, device and MQTT state, data age, database size, data coverage and the main rolling averages. A value is replaced by an explanation when the required period or minimum data coverage is not yet available.

### Analysis

The analysis view is divided into:

- **Core statistics:** mean, median, percentiles, trend, threshold duration, scientific quality, uncertainty estimate, effective sample size and confidence interval.
- **Advanced statistics:** time profiles, data quality, distribution diagnostics, threshold events, sensitivity analysis and daily tables.

All date/time profiles use the configured analysis time zone; storage remains UTC.

### Expert view

Shows raw CPH, decoder and SPIR diagnostics, firmware, campaign state, database integrity, configured conversion factor and the factor stored with historical values.

## 4. Statistical methods

The app can calculate arithmetic and geometric means, median, standard deviation, variance, quantiles, IQR, MAD, skewness, excess kurtosis, trimmed mean, Theil-Sen/Sen slope, Mann-Kendall diagnostics, autocorrelation, effective sample size, moving-block-bootstrap confidence intervals, rolling median/IQR, threshold events and concentration-class shares.

Methods are only shown when their minimum data requirements are met. Missing hours are not imputed and statistical outliers are not silently removed.

The count-based uncertainty estimate covers statistical counting variation only. It does not include calibration uncertainty, systematic device error, placement effects or environmental representativeness.

## 5. Conversion factor and traceability

`Bq/m³ = raw CPH × factor_bq_m3_per_cph`

The current configured factor is shown separately from the factor stored with each measurement. Historical values therefore remain reproducible after configuration changes. Calibration records can document laboratory, certificate, factor, uncertainty and due date.

## 6. Reports

Compact and scientific reports include the selected period, metadata, data coverage, descriptive/robust statistics, threshold metrics, charts, method notes, software version, schema version and SHA-256 checksum of the canonical selected data.

Reports are documentation aids, not official certificates.

## 7. GQ Radiation World Map

World Map upload is optional and disabled by default. A persistent queue prevents duplicate uploads and retries temporary failures. The app sends the measurement and configured GQ identifiers; it does not send GPS coordinates. Public location information remains controlled through the user’s GQ profile.

## 8. Data management

When enabled, Data management provides:

- complete backup ZIP
- CSV and diagnostics export
- database integrity information
- complete local database reset
- complete Home Assistant Recorder purge for RadonScan/Radon Monitoring entities
- supported restore workflow

The app never erases the physical history stored in the detector.

Home Assistant Recorder purge is administrator-only. A long-lived administrator token may be required in `homeassistant_access_token` when the Supervisor token is insufficient.

## 9. Main configuration

| Option | Purpose |
|---|---|
| `scan_interval` | Read-only polling interval |
| `serial_port` | Automatic or fixed serial device path |
| `factor_bq_m3_per_cph` | Current conversion factor |
| `minimum_data_coverage_percent` | Required coverage for rolling-period values |
| `analysis_timezone` | Time zone for daily/weekly analysis |
| `history_retention_days` | Local retention period |
| `gmcmap_*` | Optional World Map queue and retry settings |
| `data_management_enabled` | Show and enable destructive data tools |
| `homeassistant_access_token` | Optional administrator token for Recorder purge |
| `diagnostic_logging` | Additional diagnostic logging |

## 10. Troubleshooting

- **No device:** check USB permissions, fixed port and competing processes.
- **No new value:** only completed hours are imported; check the latest timestamp and Expert view.
- **Average unavailable:** the full period or required coverage is not present.
- **Refresh mismatch:** restart the app and reopen the Ingress panel; the frontend version must match the backend version.
- **Recorder purge fails:** verify the administrator token and Home Assistant Recorder availability.
- **World Map upload fails:** verify IDs, network, queue age and retry state.

## 11. Documentation versioning

The user manuals are versioned with the app (`4.6.0`). The separate protocol reference remains version `3.0.0` because it documents the read-only device protocol, not the app release.

## 12. Scientific and safety limitations

Short-term values and statistical relationships must not be treated as proof of causation or as a substitute for a suitable long-term measurement. Legal and health decisions require the applicable national rules and, where appropriate, qualified laboratories or authorities.
