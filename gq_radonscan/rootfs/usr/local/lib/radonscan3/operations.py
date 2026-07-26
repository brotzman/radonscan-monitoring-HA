from __future__ import annotations

import secrets
import time
from typing import Any

from .homeassistant import HomeAssistantClient
from .storage import Storage

RADON_ENTITY_GLOBS = (
    "sensor.gq_radonscan_*",
    "binary_sensor.gq_radonscan_*",
    "update.gq_radonscan_*",
    "sensor.radon_monitoring_*",
    "binary_sensor.radon_monitoring_*",
    "update.radon_monitoring_*",
    "*.radonscan_*",
)


class DataManagementOperations:
    """Orchestrates destructive operations outside the HTTP request handler."""

    def __init__(self, storage: Storage, homeassistant: HomeAssistantClient) -> None:
        self.storage = storage
        self.homeassistant = homeassistant

    def reset_database(self, user_name: str | None = None) -> dict[str, Any]:
        operation_id = secrets.token_hex(8)
        started = time.monotonic()
        result = self.storage.reset_all_data()
        result.update(
            operation_id=operation_id,
            server_duration_ms=round((time.monotonic() - started) * 1000),
        )
        return result

    def purge_home_assistant_history(self, user_name: str | None = None) -> dict[str, Any]:
        entities = self.homeassistant.radon_entities()
        entity_ids = sorted({str(item.get("entity_id") or "") for item in entities if item.get("entity_id")})
        operation_id = secrets.token_hex(8)
        started = time.monotonic()
        result = self.homeassistant.purge_entities(entity_ids, 0, list(RADON_ENTITY_GLOBS))
        result.update(
            operation_id=operation_id,
            detected_entities=len(entity_ids),
            submitted_globs=len(RADON_ENTITY_GLOBS),
            server_duration_ms=round((time.monotonic() - started) * 1000),
            verification="pending",
            note=(
                "Home Assistant accepted the recorder service request. Physical database cleanup may "
                "continue asynchronously; use the verification action after a short wait."
            ),
        )
        self.storage.set_runtime(
            "homeassistant_purge_last",
            {
                "operation_id": operation_id,
                "entity_ids": entity_ids,
                "entity_globs": list(RADON_ENTITY_GLOBS),
                "requested_at": result.get("requested_at"),
            },
        )
        self.storage.audit("homeassistant_purge_all", "recorder", result, user_name)
        return result

    def verify_home_assistant_history(self, user_name: str | None = None) -> dict[str, Any]:
        previous = self.storage.get_runtime("homeassistant_purge_last", {})
        entity_ids = previous.get("entity_ids") if isinstance(previous, dict) else []
        if not isinstance(entity_ids, list) or not entity_ids:
            entity_ids = [
                str(item.get("entity_id") or "")
                for item in self.homeassistant.radon_entities()
                if item.get("entity_id")
            ]
        result = self.homeassistant.history_summary(entity_ids)
        result.update(
            operation_id=(previous.get("operation_id") if isinstance(previous, dict) else None),
            checked_entities=len(entity_ids),
            limitation=(
                "Verification covers currently known entity IDs. Recorder rows belonging only to removed "
                "entities matched by a glob cannot be enumerated through the public history API."
            ),
        )
        self.storage.audit("homeassistant_purge_verify", "recorder", result, user_name)
        return result
