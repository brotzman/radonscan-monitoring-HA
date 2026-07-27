from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import unquote


class RoomMetadataError(ValueError):
    """Raised when room metadata cannot be normalised or validated."""


def _first(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return value[0] if value else ""
    return value


def _text(value: object) -> str:
    return " ".join(str(_first(value) or "").split())


def _extract_room(payload: Mapping[str, object]) -> str:
    for key in ("room", "name", "room_name"):
        value = _text(payload.get(key))
        if value:
            return value
    for container_key in ("location", "item", "data", "form"):
        nested = payload.get(container_key)
        if isinstance(nested, Mapping):
            value = _extract_room(nested)
            if value:
                return value
    return ""


def normalise_room_name(value: object) -> str:
    room = _text(value)
    if not room:
        raise RoomMetadataError("A room name is required")
    if len(room) > 120:
        raise RoomMetadataError("Room names may contain at most 120 characters")
    if any(ord(character) < 32 for character in room):
        raise RoomMetadataError("Room names must not contain control characters")
    return room


def parse_measurement_height(value: object) -> float | None:
    raw = _text(value)
    if not raw:
        return None
    try:
        height = float(raw.replace(",", "."))
    except ValueError as exc:
        raise RoomMetadataError("Measurement height must be a number") from exc
    if not 0.0 <= height <= 10.0:
        raise RoomMetadataError("Measurement height must be between 0 and 10 metres")
    return height


def normalise_room_record(payload: Mapping[str, object]) -> dict[str, object]:
    """Return the canonical local room record.

    Home Assistant remains authoritative for place, address and building metadata.
    Only the room name, optional measurement height and local record id survive.
    """
    room = normalise_room_name(_extract_room(payload))
    location_id = _text(payload.get("id"))
    if location_id:
        try:
            parsed_id: int | None = int(location_id)
        except ValueError as exc:
            raise RoomMetadataError("Invalid room identifier") from exc
        if parsed_id <= 0:
            raise RoomMetadataError("Invalid room identifier")
    else:
        parsed_id = None
    return {
        "id": parsed_id,
        "room": room,
        "measurement_height_m": parse_measurement_height(payload.get("measurement_height_m")),
        "active": bool(payload.get("active", True)),
    }


def merge_room_request(
    payload: Mapping[str, object] | None,
    *,
    query: Mapping[str, object] | None = None,
    headers: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Merge canonical JSON/form data with safe Ingress fallbacks.

    Some Home Assistant Ingress/proxy combinations have historically forwarded an
    empty request body. The normal request body remains authoritative. Query values
    and encoded fallback headers are used only for missing fields.
    """
    merged: dict[str, object] = dict(payload or {})
    query = query or {}
    headers = headers or {}

    if not _extract_room(merged):
        query_room = _text(query.get("room") or query.get("name") or query.get("room_name"))
        header_room = _text(headers.get("X-Radon-Room"))
        fallback_room = unquote(query_room or header_room).strip()
        if fallback_room:
            merged["room"] = fallback_room

    for key, header in (
        ("measurement_height_m", "X-Radon-Measurement-Height"),
        ("id", "X-Radon-Location-Id"),
    ):
        if _text(merged.get(key)):
            continue
        fallback = _text(query.get(key)) or _text(headers.get(header))
        if fallback:
            merged[key] = unquote(fallback)

    return normalise_room_record(merged)
