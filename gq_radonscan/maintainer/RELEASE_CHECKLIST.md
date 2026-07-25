# Release checklist

- bump `config.yaml`, Docker build argument and `radonscan3.__version__`
- update changelog, README, DOCS and both user manuals
- verify all configuration translations and interface translation keys
- run unit and release-integrity tests
- validate JavaScript and Python syntax
- render both manuals and inspect every page
- test upgrade with a copy of an existing database
- test USB import, manual refresh, backup, restore, local reset and Recorder purge in Home Assistant
- test 320 px, 390 px, tablet and desktop layouts
- build ZIP without caches and generate SHA-256
