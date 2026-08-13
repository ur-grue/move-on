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
    "google": """\
Google Gemini — Datenexport über Google Takeout

1. Öffne https://takeout.google.com
2. Klicke "Auswahl aufheben" (alle Produkte abwählen)
3. Scrolle zu "My Activity" und aktiviere nur dieses Produkt
4. Klicke "Mehrere Formate" → ändere das Format von HTML auf JSON
5. Klicke "Nächster Schritt" → wähle "Einmaliger Export"
6. Wähle als Dateityp ".zip" und eine passende Dateigröße
7. Klicke "Export erstellen"
8. Du erhältst eine E-Mail mit einem Download-Link (kann einige Stunden dauern)
9. Lade die ZIP-Datei herunter

Erwarteter Dateiname: takeout-YYYYMMDDTHHMMSS-001.zip
Die relevante Datei liegt unter: Takeout/My Activity/Gemini Apps/MyActivity.json

Wichtig: Das Format muss auf JSON gestellt werden (Schritt 4), sonst exportiert
Google die Daten als HTML.

Dann: moveon extract google <heruntergeladene-datei.zip>
""",
    "meta": """\
Meta AI — Datenexport beantragen

Option A: Über Facebook "Deine Informationen herunterladen"
1. Öffne https://accountscenter.facebook.com/info_and_permissions/dyi
2. Wähle "Informationen herunterladen"
3. Wähle das Profil und "Bestimmte Informationen auswählen"
4. Aktiviere "Nachrichten" (Messages)
5. Wähle als Format "JSON" und den gewünschten Zeitraum
6. Klicke "Anfrage senden"
7. Du erhältst eine Benachrichtigung, wenn der Download bereitsteht

Option B: Über die Meta AI App
1. Öffne die Meta AI App oder meta.ai
2. Gehe zu Menü → Einstellungen → Datenschutz und Sicherheit
3. Wähle "Deine Informationen verwalten" → "Informationen herunterladen"
4. Erstelle den Export im JSON-Format

Erwarteter Dateiname: facebook-<nutzername>-<datum>.zip
Meta AI Gespräche liegen unter: your_facebook_activity/messages/inbox/

Dann: moveon extract meta <heruntergeladene-datei.zip>
""",
    "xai": """\
xAI / Grok — Datenexport beantragen

1. Öffne https://grok.com
2. Klicke auf dein Profilbild → Settings → Data
3. Klicke "Export Data"
4. Alternativ: Öffne https://accounts.x.ai/data → "Download account data"
5. Du erhältst eine E-Mail mit einem Download-Link
6. Lade die ZIP-Datei herunter

Erwarteter Dateiname: Ein ZIP-Archiv mit prod-grok-backend.json (Konversationen)
und weiteren Dateien (Profil, Billing, Assets).

Dann: moveon extract xai <heruntergeladene-datei.zip>
""",
    "mistral": """\
Mistral AI / Le Chat — Datenexport beantragen

1. Öffne https://admin.mistral.ai/account/export
2. Klicke "Export"
3. Der Download startet automatisch als ZIP-Datei

Erwarteter Dateiname: Ein ZIP-Archiv mit chat-{uuid}.json-Dateien (eine pro Konversation)
und optionalen chat-{uuid}-files/-Verzeichnissen für Anhänge.

Hinweis: Die Konversationen haben keinen Titel im Export — Move On verwendet
die erste Nutzernachricht als Titel.

Dann: moveon extract mistral <heruntergeladene-datei.zip>
""",
    "perplexity": """\
Perplexity AI — Datenexport beantragen

1. Öffne https://www.perplexity.ai
2. Klicke auf dein Profilbild → Settings → Account
3. Scrolle zu "Export Data" und klicke den Button
4. Bestätige den Export
5. Du erhältst eine E-Mail mit einem Download-Link (verfällt nach 24 Stunden)
6. Lade die ZIP-Datei herunter

Alternative: Sende eine E-Mail an privacy@perplexity.ai mit dem Betreff
"Data Export Request" (Antwort innerhalb von 30 Tagen).

Erwarteter Dateiname: perplexity-data-export-YYYY-MM-DD.zip

Dann: moveon extract perplexity <heruntergeladene-datei.zip>
""",
}


def get_guide(provider: str) -> str | None:
    return GUIDES.get(provider)


def list_providers() -> list[str]:
    return sorted(GUIDES.keys())
