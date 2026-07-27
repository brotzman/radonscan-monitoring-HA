# Release checklist - Radon Monitoring

1. Set the same version in `config.yaml`, `Dockerfile`, package metadata, `__init__.py`, manuals, README and tests.
2. Review database migrations and confirm whether the schema version changes.
3. Run `python3 -m pytest` from the repository root.
4. Run Python compilation and JavaScript syntax checks, including every feature module.
5. Validate YAML and all JSON locale files.
6. Confirm every Home Assistant schema option has a non-empty name and description in all eight translation files.
7. Confirm every HTML and JavaScript translation key exists in every UI locale.
8. Run responsive Chromium tests at 320, 390, 768 and 1440 px, all eight languages and 200% text scaling.
9. Exercise the complete room workflow: empty-form validation, decimal comma, create, idempotent update, edit, assignment gating, assignment display, restart and Ingress body fallbacks.
10. Run the built-in System self-test and confirm that its database round trip and report-directory check leave no persistent test data.
11. Exercise local reset, Recorder purge and purge verification in the browser test.
12. Verify sensitive tokens do not appear in diagnostics, errors, reports, backups, state or self-test responses.
13. Run the three-year compact-report performance test and inspect generated PDF size.
14. Build and render German and English manuals; inspect every rendered page for clipping, overlap and broken glyphs.
15. Review `COMPATIBILITY.md` and record which environments were automated-only or field-tested.
16. Update `CHANGELOG.md` with one unambiguous release section.
17. Remove caches, temporary databases, screenshots and bytecode from the release tree.
18. Create the ZIP, test its integrity and publish a SHA-256 checksum.
19. Where hardware is available, complete the field-test matrix and record any untested limitations in the release notes.
