# Architecture

The service is split into device/protocol, storage, analysis, reporting, Home Assistant, World Map and web layers. Browser infrastructure shared by all views lives in `static/core.js`; view rendering and event wiring remain in `static/app.js`.

The SQLite schema is versioned in `storage.py`. Migrations must be additive or backed by a pre-operation backup. Raw CPH, conversion factor and source metadata must remain available for reproducibility.

Destructive browser requests require the session action token. Home Assistant Recorder purge is independent from local database reset.
