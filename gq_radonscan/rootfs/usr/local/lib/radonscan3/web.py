from __future__ import annotations

from email.parser import BytesParser
from email.policy import default as email_policy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import logging
import mimetypes
from pathlib import Path
import re
import secrets
import threading
import unicodedata
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__
from .config import Settings
from .homeassistant import HomeAssistantClient, HomeAssistantError
from .gmcmap import GmcMapClient, GmcMapError
from .i18n import LOCALE_NAMES, load, resolve
from .reports import ScientificReport
from .state import build_state
from .storage import Storage, StorageError

LOGGER = logging.getLogger(__name__)
SAFE_FILE = re.compile(r"^[A-Za-z0-9._-]+$")


def _normalise_confirmation(value: object) -> str:
    """Return a robust canonical confirmation token.

    Handles surrounding whitespace, internal whitespace, Unicode composed/decomposed
    umlauts and common punctuation copied from mobile keyboards.
    """
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.strip().upper()
    return re.sub(r"[^A-ZÄÖÜ]", "", text)


def _destructive_confirmation_ok(payload: dict[str, object], header_value: object = "") -> bool:
    confirmed = payload.get("confirmed")
    if confirmed is True or str(confirmed or "").strip().lower() in {"1", "true", "yes", "ja"}:
        return True
    tokens = (payload.get("confirmation"), payload.get("confirmation_text"), header_value)
    return any(
        _normalise_confirmation(value) in {"LÖSCHEN", "LOESCHEN", "DELETE", "PURGE", "PRURGE", "PRUGE"}
        for value in tokens
    )

class WebServer:
    def __init__(self, settings: Settings, storage: Storage) -> None:
        self.settings = settings
        self.storage = storage
        self.static_dir = Path(__file__).resolve().parent / "static"
        self.docs_dir = Path("/usr/local/share/radonscan3/docs")
        if not self.docs_dir.is_dir():
            self.docs_dir = Path(__file__).resolve().parents[2] / "share" / "radonscan3" / "docs"
        self.ha = HomeAssistantClient(settings.homeassistant_access_token)
        self.reporter = ScientificReport(storage, settings)
        self.gmcmap = GmcMapClient(settings, storage)
        self.csrf_token = secrets.token_urlsafe(24)
        self.server = ThreadingHTTPServer(("0.0.0.0", settings.web_port), self._handler())
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, name="radon-monitoring-web", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _handler(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            server_version = f"Radon-Monitoring/{__version__}"

            def log_message(self, fmt: str, *args) -> None:
                LOGGER.debug("web: " + fmt, *args)

            @property
            def user_name(self) -> str | None:
                return self.headers.get("X-Remote-User-Display-Name") or self.headers.get("X-Remote-User-Name")

            def require_data_management(self) -> None:
                if not app.settings.data_management_enabled:
                    raise StorageError("Data management is disabled in the app configuration")

            def send_bytes(
                self,
                data: bytes,
                content_type: str,
                status: int = 200,
                *,
                disposition: str | None = None,
                cache: str = "no-store",
            ) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", cache)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Frame-Options", "SAMEORIGIN")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; style-src 'self'; script-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
                    "form-action 'self'; frame-ancestors 'self'",
                )
                if disposition:
                    self.send_header("Content-Disposition", disposition)
                self.end_headers()
                self.wfile.write(data)

            def json_response(self, payload: object, status: int = 200, *, disposition: str | None = None) -> None:
                self.send_bytes(
                    json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                    "application/json; charset=utf-8",
                    status,
                    disposition=disposition,
                )

            def error_response(self, message: str, status: int = 400, **extra) -> None:
                self.json_response({"ok": False, "error": message, **extra}, status)

            def locale(self, query: dict[str, list[str]]) -> str:
                requested = str((query.get("lang") or [app.settings.language])[0])
                return resolve(requested, self.headers.get("Accept-Language"))

            def query_int(self, query: dict[str, list[str]], name: str, default: int | None = None) -> int | None:
                value = (query.get(name) or [""])[0]
                if value == "":
                    return default
                try:
                    return int(value)
                except ValueError:
                    return default

            def read_body(self, max_bytes: int | None = None) -> bytes:
                limit = max_bytes or 2 * 1024 * 1024
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    raise StorageError("Invalid content length")
                if length <= 0:
                    return b""
                if length > limit:
                    raise StorageError("Request body is too large")
                return self.rfile.read(length)

            def read_json(self) -> dict[str, object]:
                body = self.read_body(4 * 1024 * 1024)
                if not body:
                    return {}
                try:
                    payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise StorageError("Invalid JSON request") from exc
                if not isinstance(payload, dict):
                    raise StorageError("JSON body must be an object")
                return payload

            def read_multipart(self, max_bytes: int | None = None) -> tuple[dict[str, str], dict[str, tuple[str, str, bytes]]]:
                content_type = self.headers.get("Content-Type", "")
                if "multipart/form-data" not in content_type:
                    raise StorageError("multipart/form-data is required")
                body = self.read_body(max_bytes)
                envelope = (
                    f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
                )
                message = BytesParser(policy=email_policy).parsebytes(envelope)
                fields: dict[str, str] = {}
                files: dict[str, tuple[str, str, bytes]] = {}
                if not message.is_multipart():
                    raise StorageError("Invalid multipart request")
                for part in message.iter_parts():
                    name = part.get_param("name", header="content-disposition")
                    if not name:
                        continue
                    filename = part.get_filename()
                    content = part.get_payload(decode=True) or b""
                    if filename:
                        files[str(name)] = (
                            Path(filename).name,
                            part.get_content_type() or "application/octet-stream",
                            content,
                        )
                    else:
                        fields[str(name)] = content.decode(part.get_content_charset() or "utf-8", "replace")
                return fields, files

            def require_write_token(self) -> bool:
                token = self.headers.get("X-Radon-Action", "")
                if token != app.csrf_token:
                    self.error_response("Write request rejected", 403)
                    return False
                return True

            def serve_file(self, path: Path, content_type: str | None = None, disposition: str | None = None) -> None:
                if not path.is_file():
                    self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
                    return
                mime = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                self.send_bytes(path.read_bytes(), mime, disposition=disposition)

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                query = parse_qs(parsed.query)

                try:
                    if path == "/":
                        locale = self.locale(query)
                        template = (app.static_dir / "index.html").read_text(encoding="utf-8")
                        body = (
                            template.replace("__LOCALE__", locale)
                            .replace("__VERSION__", __version__)
                            .replace("__TRANSLATIONS__", json.dumps(load(locale), ensure_ascii=False))
                            .replace("__LOCALE_NAMES__", json.dumps(LOCALE_NAMES, ensure_ascii=False))
                            .replace("__ACTION_TOKEN__", app.csrf_token)
                        )
                        self.send_bytes(body.encode("utf-8"), "text/html; charset=utf-8")
                        return

                    if path.startswith("/assets/"):
                        name = path.split("/", 2)[-1]
                        if name not in {"app.css", "app.js", "icon.png"}:
                            self.send_bytes(b"Not found", "text/plain", 404)
                            return
                        file_path = app.static_dir / name
                        if name == "icon.png" and not file_path.is_file():
                            file_path = Path("/usr/local/share/radonscan3/icon.png")
                        content_type = {
                            ".css": "text/css; charset=utf-8",
                            ".js": "application/javascript; charset=utf-8",
                            ".png": "image/png",
                        }.get(file_path.suffix, "application/octet-stream")
                        self.send_bytes(file_path.read_bytes(), content_type, cache="no-store")
                        return

                    if path == "/api/state":
                        state = build_state(app.storage, app.settings)
                        state["homeassistant"] = app.ha.status()
                        self.json_response(state)
                        return

                    if path == "/api/history":
                        self.json_response({"items": app.storage.history(
                            limit=self.query_int(query, "limit", 500) or 500,
                            days=self.query_int(query, "days"),
                            start=(query.get("start") or [None])[0],
                            end=(query.get("end") or [None])[0],
                            location_id=self.query_int(query, "location_id"),
                            campaign_id=self.query_int(query, "campaign_id"),
                            device_id=(query.get("device_id") or [None])[0],
                            ascending=((query.get("order") or ["desc"])[0] == "asc"),
                        )})
                        return

                    if path == "/api/analysis":
                        requested_tz = (query.get("timezone") or [app.settings.analysis_timezone])[0]
                        if requested_tz == "auto":
                            ha_status = app.ha.status()
                            requested_tz = str(ha_status.get("time_zone") or "UTC")
                        result = app.storage.analysis(
                            start=(query.get("start") or [None])[0],
                            end=(query.get("end") or [None])[0],
                            days=self.query_int(query, "days", 30),
                            location_id=self.query_int(query, "location_id"),
                            campaign_id=self.query_int(query, "campaign_id"),
                            device_id=(query.get("device_id") or [None])[0],
                            warning_threshold=app.settings.warning_threshold_bq_m3,
                            danger_threshold=app.settings.danger_threshold_bq_m3,
                            minimum_coverage_percent=app.settings.minimum_data_coverage_percent,
                            timezone_name=requested_tz,
                        )
                        self.json_response(result)
                        return

                    if path == "/api/catalog":
                        self.json_response({
                            "locations": app.storage.locations(),
                            "sessions": app.storage.sessions(),
                            "campaigns": app.storage.campaigns(),
                            "devices": app.storage.devices(),
                            "events": app.storage.events(),
                            "reports": app.storage.reports(),
                            "factor_history": app.storage.factor_history(),
                            "calibrations": app.storage.calibrations(),
                            "campaign_protocols": app.storage.campaign_protocols(),
                        })
                        return

                    if path == "/api/gmcmap/upload":
                        payload = self.read_json()
                        confirmation = str(payload.get("confirmation") or "").strip().upper()
                        if confirmation not in {"UPLOAD", "HOCHLADEN"}:
                            raise GmcMapError("Upload confirmation is required")
                        result = app.gmcmap.upload_latest(trigger="manual", user_name=self.user_name)
                        self.json_response({"ok": True, "result": result})
                        return

                    if path == "/api/locations":
                        self.json_response({"items": app.storage.locations()})
                        return
                    if path == "/api/sessions":
                        self.json_response({"items": app.storage.sessions()})
                        return
                    if path == "/api/events":
                        self.json_response({"items": app.storage.events(
                            start=(query.get("start") or [None])[0],
                            end=(query.get("end") or [None])[0],
                            location_id=self.query_int(query, "location_id"),
                        )})
                        return
                    if path == "/api/reports":
                        self.json_response({"items": app.storage.reports()})
                        return
                    if path == "/api/gmcmap":
                        self.json_response({"status": app.gmcmap.status(), "uploads": app.storage.worldmap_uploads(self.query_int(query, "limit", 100) or 100)})
                        return
                    if path == "/api/factors":
                        self.json_response({"items": app.storage.factor_history((query.get("device_id") or [None])[0], self.query_int(query, "limit", 100) or 100)})
                        return
                    if path == "/api/calibrations":
                        self.json_response({"items": app.storage.calibrations((query.get("device_id") or [None])[0])})
                        return
                    if path == "/api/campaign-protocols":
                        self.json_response({"items": app.storage.campaign_protocols()})
                        return
                    if path == "/api/data/summary":
                        self.require_data_management()
                        self.json_response(app.storage.data_summary())
                        return
                    if path == "/api/audit":
                        self.require_data_management()
                        self.json_response({"items": app.storage.audit_entries(self.query_int(query, "limit", 200) or 200)})
                        return
                    if path == "/api/homeassistant/status":
                        self.json_response(app.ha.status())
                        return
                    if path == "/api/homeassistant/entities":
                        self.require_data_management()
                        self.json_response({"items": app.ha.radon_entities()})
                        return

                    if path == "/api/diagnostics":
                        payload = {
                            "state": build_state(app.storage, app.settings),
                            "runtime": app.storage.runtime_all(),
                            "data": app.storage.data_summary(),
                            "campaigns": app.storage.campaigns(),
                            "locations": app.storage.locations(),
                        }
                        self.json_response(payload, disposition='attachment; filename="radon-monitoring-diagnostics.json"')
                        return

                    if path == "/health":
                        state = build_state(app.storage, app.settings)
                        connected = bool(state.get("connection", {}).get("connected"))
                        payload = {
                            "status": "ok" if connected or state["database"]["sample_count"] > 0 else "starting",
                            "connected": connected,
                            "version": __version__,
                        }
                        self.json_response(payload, 200)
                        return

                    if path == "/export/history.csv":
                        filename = "radon-monitoring-hourly-history.csv"
                        self.send_bytes(
                            app.storage.csv_bytes(
                                start=(query.get("start") or [None])[0],
                                end=(query.get("end") or [None])[0],
                                location_id=self.query_int(query, "location_id"),
                                device_id=(query.get("device_id") or [None])[0],
                            ),
                            "text/csv; charset=utf-8",
                            disposition=f'attachment; filename="{filename}"',
                        )
                        return

                    if path == "/export/backup.zip":
                        self.require_data_management()
                        self.send_bytes(
                            app.storage.backup_zip_bytes(),
                            "application/zip",
                            disposition='attachment; filename="radon-monitoring-backup.zip"',
                        )
                        return

                    if path.startswith("/reports/"):
                        report_id = unquote(path.split("/reports/", 1)[1])
                        item = app.storage.report(report_id)
                        if not item:
                            self.send_bytes(b"Not found", "text/plain", 404)
                            return
                        filename = str(item["filename"])
                        if not SAFE_FILE.fullmatch(filename):
                            self.send_bytes(b"Not found", "text/plain", 404)
                            return
                        self.serve_file(
                            app.storage.reports_dir / filename,
                            "application/pdf",
                            disposition=f'inline; filename="{filename}"',
                        )
                        return

                    if path in {"/docs/user-manual.pdf", "/docs/protocol-reference.pdf"}:
                        locale = self.locale(query)
                        prefix = "Radon_Monitoring_User_Manual_4.2.1" if "user-manual" in path else "GQ_RadonScan_Protocol_Reference_3.0.0"
                        candidates = [app.docs_dir / f"{prefix}_{locale}.pdf", app.docs_dir / f"{prefix}_en.pdf"]
                        manual = next((candidate for candidate in candidates if candidate.is_file()), None)
                        if manual is None:
                            self.send_bytes(b"Document not found", "text/plain", 404)
                            return
                        self.send_bytes(manual.read_bytes(), "application/pdf", disposition=f'inline; filename="{manual.name}"')
                        return

                    self.send_bytes(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
                except (StorageError, HomeAssistantError, GmcMapError, ValueError) as exc:
                    LOGGER.warning("GET %s failed: %s", path, exc)
                    self.error_response(str(exc), 400)
                except Exception as exc:
                    LOGGER.exception("GET %s failed", path)
                    self.error_response("Internal server error", 500)

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                if not self.require_write_token():
                    return
                try:
                    if path == "/api/gmcmap/retry":
                        count = app.storage.retry_worldmap_failures()
                        app.storage.audit("gmcmap_retry", "gmcmap", {"count": count}, self.user_name)
                        self.json_response({"ok": True, "retried": count})
                        return

                    if path == "/api/locations":
                        item = app.storage.save_location(self.read_json())
                        self.json_response({"ok": True, "item": item}, 201)
                        return

                    if path == "/api/locations/assign":
                        payload = self.read_json()
                        result = app.storage.assign_location(
                            location_id=int(payload.get("location_id") or 0),
                            start=str(payload.get("start") or ""),
                            end=str(payload.get("end") or "") or None,
                            title=str(payload.get("title") or "Measurement session"),
                            purpose=str(payload.get("purpose") or ""),
                            responsible=str(payload.get("responsible") or ""),
                            notes=str(payload.get("notes") or ""),
                            device_id=str(payload.get("device_id") or "") or None,
                            user_name=self.user_name,
                        )
                        self.json_response({"ok": True, **result}, 201)
                        return

                    if path == "/api/events":
                        item = app.storage.add_event(self.read_json(), self.user_name)
                        self.json_response({"ok": True, "item": item}, 201)
                        return

                    if path == "/api/calibrations":
                        self.json_response({"ok": True, "item": app.storage.add_calibration(self.read_json(), self.user_name)})
                        return
                    if path == "/api/campaign-protocols":
                        self.json_response({"ok": True, "item": app.storage.save_campaign_protocol(self.read_json(), self.user_name)})
                        return
                    if path == "/api/reports":
                        item = app.reporter.create(self.read_json())
                        self.json_response({"ok": True, "item": item}, 201)
                        return

                    if path == "/api/data/reset":
                        self.require_data_management()
                        result = app.storage.reset_all_data()
                        self.json_response({"ok": True, **result})
                        return

                    if path == "/api/data/delete":
                        self.require_data_management()
                        raise StorageError("Selective deletion is no longer available. Use complete database deletion.")

                    if path == "/api/data/restore":
                        self.require_data_management()
                        fields, files = self.read_multipart(251 * 1024 * 1024)
                        if fields.get("confirmation", "").strip().upper() not in {"RESTORE", "WIEDERHERSTELLEN"}:
                            raise StorageError("Restore confirmation is required")
                        if "file" not in files:
                            raise StorageError("A database or backup ZIP is required")
                        filename, _, data = files["file"]
                        result = app.storage.restore_database(data, filename, self.user_name)
                        self.json_response({"ok": True, **result})
                        return

                    if path == "/api/homeassistant/purge-all":
                        self.require_data_management()
                        entities = app.ha.radonscan_entities()
                        entity_ids = [str(item.get("entity_id") or "") for item in entities]
                        entity_globs = [
                            "sensor.gq_radonscan_*",
                            "binary_sensor.gq_radonscan_*",
                            "update.gq_radonscan_*",
                            "sensor.radon_monitoring_*",
                            "binary_sensor.radon_monitoring_*",
                            "update.radon_monitoring_*",
                            "*.radonscan_*",
                        ]
                        result = app.ha.purge_entities(entity_ids, 0, entity_globs)
                        app.storage.audit("homeassistant_purge_all", "recorder", result, self.user_name)
                        self.json_response({"ok": True, **result})
                        return

                    if path == "/api/homeassistant/purge":
                        self.require_data_management()
                        raise StorageError("Selective recorder deletion is no longer available. Use complete RadonScan history deletion.")

                    self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
                except (StorageError, HomeAssistantError, GmcMapError, ValueError, KeyError) as exc:
                    LOGGER.warning("POST %s failed: %s", path, exc)
                    self.error_response(str(exc), 400)
                except Exception:
                    LOGGER.exception("POST %s failed", path)
                    self.error_response("Internal server error", 500)

            def do_DELETE(self) -> None:
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                query = parse_qs(parsed.query)
                if not self.require_write_token():
                    return
                try:
                    if path.startswith("/api/locations/"):
                        deleted = app.storage.delete_location(int(path.rsplit("/", 1)[-1]), user_name=self.user_name)
                    elif path.startswith("/api/events/"):
                        deleted = app.storage.delete_event(int(path.rsplit("/", 1)[-1]), self.user_name)
                    elif path.startswith("/api/reports/"):
                        deleted = app.storage.delete_report(unquote(path.rsplit("/", 1)[-1]), self.user_name)
                    else:
                        self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
                        return
                    self.json_response({"ok": True, "deleted": deleted})
                except (StorageError, ValueError) as exc:
                    self.error_response(str(exc), 400)
                except Exception:
                    LOGGER.exception("DELETE %s failed", path)
                    self.error_response("Internal server error", 500)

        return Handler
