from __future__ import annotations

import json
from pathlib import Path

SUPPORTED = ("de", "en", "es", "fr", "hr", "it", "nl", "pl")
LOCALE_NAMES = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "hr": "Hrvatski",
    "it": "Italiano",
    "nl": "Nederlands",
    "pl": "Polski",
}


def normalize(value: str | None) -> str:
    raw = (value or "").strip().lower().replace("_", "-")
    base = raw.split("-", 1)[0]
    return base if base in SUPPORTED else "en"


def resolve(requested: str, accept_language: str | None = None) -> str:
    if requested and requested != "auto":
        return normalize(requested)
    if accept_language:
        for token in accept_language.split(","):
            candidate = normalize(token.split(";", 1)[0])
            if candidate in SUPPORTED:
                return candidate
    return "en"


def load(locale: str) -> dict[str, str]:
    code = normalize(locale)
    root = Path(__file__).resolve().parent / "locales"
    fallback = json.loads((root / "en.json").read_text(encoding="utf-8"))
    if code == "en":
        return fallback
    try:
        localized = json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
        return {**fallback, **localized}
    except Exception:
        return fallback
