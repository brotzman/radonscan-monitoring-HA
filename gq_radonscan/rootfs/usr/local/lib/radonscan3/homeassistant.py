from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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
            raise HomeAssistantError(f"Home Assistant returned HTTP {exc.code}: {body[:500]}") from exc
        except URLError as exc:
            raise HomeAssistantError(f"Home Assistant is not reachable: {exc.reason}") from exc

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
            "response": response,
        }
