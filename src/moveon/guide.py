from __future__ import annotations

GUIDES: dict[str, str] = {
    "openai": """\
OpenAI / ChatGPT — Datenexport beantragen

1. Öffne https://chatgpt.com
2. Klicke auf dein Profilbild (unten links) → Settings
3. Wähle "Data controls"
4. Klicke "Export data" → "Confirm export"
5. Du erhältst eine E-Mail mit einem Download-Link (kann bis zu 24h dauern)
6. Lade die ZIP-Datei herunter

Erwarteter Dateiname: Ein ZIP-Archiv mit conversations.json und weiteren Dateien.

Dann: moveon extract openai <heruntergeladene-datei.zip>
""",
    "anthropic": """\
Anthropic / Claude — Datenexport beantragen

1. Öffne https://claude.ai
2. Klicke auf dein Profilbild → Settings
3. Wähle "Account" → "Export Data"
4. Bestätige den Export
5. Du erhältst eine E-Mail mit einem Download-Link
6. Lade die ZIP-Datei herunter

Erwarteter Dateiname: Ein ZIP-Archiv mit Konversationsdaten.

Dann: moveon extract anthropic <heruntergeladene-datei.zip>
""",
}


def get_guide(provider: str) -> str | None:
    return GUIDES.get(provider)


def list_providers() -> list[str]:
    return sorted(GUIDES.keys())
