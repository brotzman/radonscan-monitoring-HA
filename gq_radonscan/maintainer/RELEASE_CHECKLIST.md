# Release checklist - Radon Monitoring

1. Set the same version in `config.yaml`, `Dockerfile`, package metadata, `__init__.py`, manuals, README and tests.
2. Review database migrations and confirm whether the schema version changes.
3. Run `python3 -m pytest` from the repository root.
4. Run Python compilation and JavaScript syntax checks.
5. Validate YAML and all JSON locale files.
6. Confirm every Home Assistant schema option has a non-empty name and description in all eight translation files.
7. Confirm every HTML and JavaScript translation key exists in every UI locale.
8. Run responsive Chromium tests at 320, 390, 768 and 1440 px, all eight languages and 200% text scaling.
9. Exercise local reset, Recorder purge and purge verification in the browser test.
10. Verify sensitive tokens do not appear in diagnostics, errors, reports, backups or state responses.
11. Run the three-year compact-report performance test and inspect generated PDF size.
12. Build and render German and English manuals; inspect every rendered page for clipping, overlap and broken glyphs.
13. Update `CHANGELOG.md` with one unambiguous release section.
14. Remove caches, temporary databases, screenshots and bytecode from the release tree.
15. Create the ZIP, test its integrity and publish a SHA-256 checksum.
16. Where hardware is available, complete the field-test matrix and record any untested limitations in the release notes.
