# Move On

**Hol deine Daten. Lösch dich raus.**

Move On extrahiert deine KI-Chatverläufe aus proprietären Anbietern (OpenAI, Anthropic) in ein offenes Format und generiert versandfertige DSGVO-Löschanträge.

Kein Netzwerkzugriff. Keine Telemetrie. Keine Anbieter-Logins.

## Installation

```bash
pip install moveon
```

Oder aus dem Repo:

```bash
pip install -e ".[dev]"
```

## Benutzung

```bash
# 1. Anleitung zum Datenexport
moveon guide openai

# 2. Export entpacken und normalisieren
moveon extract openai ~/Downloads/export.zip

# 3. Löschanträge generieren
moveon erase --all

# 4. Status prüfen
moveon status
```

## Was passiert

1. **Extract** parst den Export-ZIP deines Anbieters und normalisiert die Chatverläufe in JSONL.
2. **Erase** generiert vorformulierte DSGVO-Löschanträge (Art. 17) in Deutsch und Englisch.
3. **Status** zeigt eine Übersicht: welche Provider extrahiert wurden, wie viele Konversationen, wann.

Alles landet in `MOVEON.d/` — einem lokalen Bundle, das nie das Internet sieht.

## Provider

| Provider | Extract | Erase |
|----------|---------|-------|
| OpenAI (ChatGPT) | ✓ | ✓ |
| Anthropic (Claude) | ✓ | ✓ |

Weitere Provider via Plugin-Interface erweiterbar.

## Sicherheit

- Kein Netzwerkzugriff zur Laufzeit (verifiziert durch Socket-Blockade-Tests)
- `MOVEON.d/` wird mit restriktiven Dateiberechtigungen erstellt (0700/0600)
- Automatische `.gitignore` verhindert versehentliches Committen
- Alle Dependencies auditierbar, keine Telemetrie

## Lizenz

MIT
