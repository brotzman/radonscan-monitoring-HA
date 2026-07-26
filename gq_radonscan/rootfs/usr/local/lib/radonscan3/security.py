from __future__ import annotations

import re
from typing import Any, Iterable

_SENSITIVE_KEY_PARTS = (
    "token",
    "password",
    "secret",
    "authorization",
    "api_key",
)


def is_sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key or "").strip().lower())
    if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
        return True
    return normalized in {"gmcmap_account_id", "gmcmap_device_id"}


def redact_sensitive(value: Any, *, extra_secrets: Iterable[str] = ()) -> Any:
    """Return a JSON-compatible copy with credentials and identifiers removed.

    The function is deliberately conservative. It is used for diagnostics and error
    reporting, where omitting a value is preferable to leaking a credential.
    """
    secrets = tuple(secret for secret in (str(item) for item in extra_secrets) if secret)

    def clean(item: Any, key: object | None = None) -> Any:
        if key is not None and is_sensitive_key(key):
            return "<redacted>"
        if isinstance(item, dict):
            return {str(k): clean(v, k) for k, v in item.items()}
        if isinstance(item, (list, tuple, set)):
            return [clean(entry) for entry in item]
        if isinstance(item, str):
            text = item
            for secret in secrets:
                text = text.replace(secret, "<redacted>")
            # Also remove accidental bearer values from upstream error bodies.
            text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<redacted>", text)
            return text
        return item

    return clean(value)


def safe_error_message(message: object, *secrets: str) -> str:
    return str(redact_sensitive(str(message), extra_secrets=secrets))
