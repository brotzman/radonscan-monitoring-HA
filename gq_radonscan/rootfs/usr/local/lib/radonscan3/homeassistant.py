from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .security import safe_error_message


class HomeAssistantError(RuntimeError):
    pass


class HomeAssistantClient:
    def __init__(self, access_token: str = "") -> None:
        configured_token = str(access_token).strip()
        self.token_source = "homeassistant_access_token" if configured_token else "supervisor_token"
        self.token = configured_token or os.environ.get("SUPERVISOR_TOKEN", "")
        # Long-lived Home Assistant tokens authenticate directly against Core.
        # The Supervisor proxy is used only with the add-on Supervisor token.
        default_url = "http://homeassistant:8123/api" if configured_token else "http://supervisor/core/api"
        self.base_url = os.environ.get("HOME_ASSISTANT_API_URL", default_url).rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self.token)

    def _request(self, method: str, path: str, payload: object | None = None) -> Any:
        if not self.token:
            raise HomeAssistantError("SUPERVISOR_TOKEN is not available")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            message = safe_error_message(f"Home Assistant returned HTTP {exc.code}: {body[:500]}", self.token)
            raise HomeAssistantError(message) from exc
        except URLError as exc:
            raise HomeAssistantError(safe_error_message(f"Home Assistant is not reachable: {exc.reason}", self.token)) from exc

    def status(self) -> dict[str, object]:
        if not self.available:
            return {"available": False, "connected": False, "error": "token_missing"}
        try:
            config = self._request("GET", "config")
            return {
                "available": True,
                "connected": True,
                "version": config.get("version"),
                "location_name": config.get("location_name"),
                "time_zone": config.get("time_zone"),
            }
        except HomeAssistantError as exc:
            return {"available": True, "connected": False, "error": str(exc)}

    def radon_entities(self) -> list[dict[str, object]]:
        states = self._request("GET", "states")
        candidates: list[dict[str, object]] = []
        for item in states if isinstance(states, list) else []:
            entity_id = str(item.get("entity_id") or "")
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            friendly = str(attrs.get("friendly_name") or "")
            device_class = str(attrs.get("device_class") or "")
            unit = str(attrs.get("unit_of_measurement") or "")
            haystack = f"{entity_id} {friendly}".lower()
            relevant = (
                "radon" in haystack
                or "gq_radonscan" in haystack
                or device_class == "radon"
                or ("cph" in haystack and entity_id.startswith("sensor."))
            )
            if not relevant:
                continue
            candidates.append(
                {
                    "entity_id": entity_id,
                    "friendly_name": friendly or entity_id,
                    "state": item.get("state"),
                    "unit": unit,
                    "device_class": device_class,
                    "last_updated": item.get("last_updated"),
                    "recommended": (
                        device_class == "radon"
                        or "gq_radonscan" in haystack
                        or "radon_monitoring" in haystack
                    ),
                }
            )
        return sorted(candidates, key=lambda item: (not bool(item["recommended"]), str(item["entity_id"])))


    def fire_event(self, event_type: str, event_data: dict[str, object] | None = None) -> dict[str, object]:
        cleaned = "".join(ch for ch in str(event_type).lower() if ch.isalnum() or ch == "_").strip("_")
        if not cleaned:
            raise HomeAssistantError("Invalid event type")
        return self._request("POST", f"events/{cleaned}", event_data or {})

    def history_summary(
        self,
        entity_ids: list[str],
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        chunk_size: int = 20,
    ) -> dict[str, object]:
        """Count historical rows for known entities using Home Assistant's public REST API.

        The check deliberately ends five minutes before the request by default so a current
        post-purge state does not look like old history. It verifies known entity IDs only.
        """
        cleaned = sorted({str(entity).strip() for entity in entity_ids if str(entity).strip()})
        if not cleaned:
            return {
                "verified": False,
                "status": "no_entities",
                "remaining_rows": 0,
                "entities_with_history": [],
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        now = datetime.now(timezone.utc)
        period_start = start or datetime(2000, 1, 1, tzinfo=timezone.utc)
        period_end = end or (now - timedelta(minutes=5))
        if period_end <= period_start:
            raise HomeAssistantError("History verification period is invalid")

        counts: dict[str, int] = {entity: 0 for entity in cleaned}
        for offset in range(0, len(cleaned), max(1, int(chunk_size))):
            chunk = cleaned[offset : offset + max(1, int(chunk_size))]
            params = urlencode(
                {
                    "filter_entity_id": ",".join(chunk),
                    "end_time": period_end.isoformat(),
                }
            )
            payload = self._request(
                "GET",
                f"history/period/{quote(period_start.isoformat(), safe='')}?{params}&minimal_response&no_attributes",
            )
            if not isinstance(payload, list):
                continue
            for series in payload:
                if not isinstance(series, list) or not series:
                    continue
                first = series[0] if isinstance(series[0], dict) else {}
                entity_id = str(first.get("entity_id") or "")
                if entity_id in counts:
                    counts[entity_id] += len(series)

        remaining = sum(counts.values())
        with_history = [entity for entity, count in counts.items() if count > 0]
        return {
            "verified": remaining == 0,
            "status": "complete" if remaining == 0 else "history_remaining",
            "remaining_rows": remaining,
            "entities_with_history": with_history,
            "per_entity": counts,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "checked_at": now.isoformat(),
        }

    def purge_entities(
        self,
        entity_ids: list[str] | None = None,
        keep_days: int = 0,
        entity_globs: list[str] | None = None,
    ) -> dict[str, object]:
        cleaned = sorted({str(entity).strip() for entity in (entity_ids or []) if str(entity).strip()})
        globs = sorted({str(pattern).strip() for pattern in (entity_globs or []) if str(pattern).strip()})
        if not cleaned and not globs:
            raise HomeAssistantError("At least one entity or entity glob is required")
        for entity_id in cleaned:
            if "." not in entity_id or any(char.isspace() for char in entity_id):
                raise HomeAssistantError(f"Invalid entity ID: {entity_id}")
        keep_days = max(0, min(3650, int(keep_days)))
        payload: dict[str, object] = {"keep_days": keep_days}
        if cleaned:
            payload["entity_id"] = cleaned
        if globs:
            payload["entity_globs"] = globs
        response = self._request("POST", "services/recorder/purge_entities", payload)
        return {
            "requested": True,
            "entity_ids": cleaned,
            "entity_globs": globs,
            "keep_days": keep_days,
            "authentication": self.token_source,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "response": response,
        }
