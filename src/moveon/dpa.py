from __future__ import annotations

import json
from pathlib import Path

_DPA_DATA: list[dict] | None = None

PROVIDER_JURISDICTIONS: dict[str, str] = {
    "openai": "IE",
    "anthropic": "IE",
    "google": "IE",
    "meta": "IE",
    "xai": "IE",
    "mistral": "FR",
    "perplexity": "IE",
}


def _load_dpa_data() -> list[dict]:
    global _DPA_DATA
    if _DPA_DATA is None:
        data_path = Path(__file__).parent / "data" / "dpa.json"
        _DPA_DATA = json.loads(data_path.read_text(encoding="utf-8"))
    return _DPA_DATA


def get_dpa(country_code: str) -> dict | None:
    code = country_code.upper()
    for entry in _load_dpa_data():
        if entry["country_code"] == code:
            return entry
    return None


def get_dpa_for_provider(provider: str, country: str | None = None) -> dict | None:
    if country:
        return get_dpa(country)
    code = PROVIDER_JURISDICTIONS.get(provider)
    if code:
        return get_dpa(code)
    return None


def list_countries() -> list[str]:
    return [e["country_code"] for e in _load_dpa_data()]
