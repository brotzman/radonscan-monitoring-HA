# Testing

Run from the add-on directory with the library on `PYTHONPATH`:

```bash
PYTHONPATH=rootfs/usr/local/lib python -m unittest discover -s tests -v
```

Release checks cover analysis, scientific metadata, storage migration, confirmation handling, Home Assistant purge payloads, static asset loading, translation completeness, duplicate HTML IDs and documentation/version consistency.

Hardware, Home Assistant Ingress and external World Map field tests remain mandatory before broad release.
