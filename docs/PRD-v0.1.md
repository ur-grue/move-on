# PRD: Move On v0.1 — Extract + Erase

<!-- Loki-Mode-optimiert: messbare Ziele, FR-Format, Given/When/Then, deterministische Completion-Checkliste. -->
<!-- Scope: NUR v0.1 (Extract + Erase). Distill (v0.2) und Deploy (v1.0) sind explizit AUSGESCHLOSSEN. -->

## Product Summary

Move On ist ein Python-CLI-Tool, das offizielle Datenexporte proprietärer KI-Anbieter (OpenAI/ChatGPT, Anthropic/Claude) in ein offenes, anbieterneutrales Format normalisiert und versandfertige DSGVO-Löschanträge (Art. 17) generiert. Kein Netzwerkzugriff, keine Telemetrie, keine Anbieter-Logins.

**Elevator pitch:** "Hol deine Daten. Lösch dich raus."

## Tech Stack (verbindlich)

- Python ≥3.11, Paketstruktur `src/moveon/`, Packaging via `pyproject.toml` (hatchling oder setuptools)
- CLI-Framework: Typer
- Datenmodelle: Pydantic v2
- Tests: pytest, Testdaten als Fixtures in `tests/fixtures/` (synthetische Beispiel-Exporte, KEINE echten Nutzerdaten)
- Ausgabeformat facts/messages: JSONL nach Mem0-Importschema (Provenienz in `metadata`-Feldern)
- Lizenz: MIT (`LICENSE`-Datei im Repo-Root)
- Keine externen API-Calls, keine Telemetrie, keine Netzwerkzugriffe zur Laufzeit

## CLI-Oberfläche (verbindlich)

```
moveon extract <provider> <export.zip> [--out DIR]   # provider: openai | anthropic
moveon guide <provider>                              # zeigt an, wo der Export beantragt wird
moveon erase <provider> [--lang de|en] [--out DIR]   # generiert Löschantrag
moveon erase --all [--lang de|en]
moveon status                                        # zeigt Manifest-Inhalt: Quellen, Datum, Hashes
```

Alle Ausgaben landen im Bundle-Verzeichnis `MOVEON.d/` (Default: `./MOVEON.d/`, überschreibbar via `--out`).

## Bundle-Struktur (verbindlich)

```
MOVEON.d/
├── raw/
│   ├── openai/messages.jsonl        # normalisierte Nachrichten
│   └── anthropic/messages.jsonl
├── erase/
│   ├── openai-erasure-de.md         # Löschantrag deutsch
│   ├── openai-erasure-en.md
│   ├── anthropic-erasure-de.md
│   ├── anthropic-erasure-en.md
│   └── TRACKING.md                  # Fristen-Checkliste
└── manifest.json                    # Quellen, Exportdatum, SHA-256-Hashes, Toolversion
```

Schema `messages.jsonl` (eine Zeile pro Nachricht):
```json
{"messages": [{"role": "user", "content": "..."}], "metadata": {"source": "openai", "conversation_id": "...", "conversation_title": "...", "timestamp": "ISO-8601"}}
```

## Functional Requirements

### FR-1: Extract OpenAI
Parst das offizielle ChatGPT-Datenexport-ZIP (enthält `conversations.json`).

- Given ein valides ChatGPT-Export-ZIP, When `moveon extract openai export.zip`, Then existiert `MOVEON.d/raw/openai/messages.jsonl` mit einer JSONL-Zeile pro Nachricht und ein Eintrag in `manifest.json` mit SHA-256 des Quell-ZIPs.
- Given ein Export mit verschachtelten Konversationsbäumen (ChatGPT-`mapping`-Struktur mit Branches), When extract läuft, Then wird der aktive Pfad (current_node-Kette) extrahiert; verworfene Branches werden gezählt und im CLI-Output als Zahl ausgewiesen.
- Given eine korrupte oder nicht als ChatGPT-Export erkennbare ZIP, When extract läuft, Then Exit-Code 1 und eine Fehlermeldung, die Datei und Grund benennt; `MOVEON.d/` bleibt unverändert.
- Given ein Export mit Nicht-Text-Inhalten (Bilder, Audio-Referenzen), When extract läuft, Then werden diese als `{"content": "[non-text content: <type>]"}` platzhalter-kodiert statt das Parsing abzubrechen.

### FR-2: Extract Anthropic
Parst das offizielle Claude-Datenexport-Archiv (conversations.json-Struktur des Claude-Exports).

- Given ein valides Claude-Export-Archiv, When `moveon extract anthropic export.zip`, Then existiert `MOVEON.d/raw/anthropic/messages.jsonl` analog FR-1.
- Given beide Provider wurden extrahiert, When `moveon status`, Then listet die Ausgabe beide Quellen mit Exportdatum, Nachrichtenzahl und Hash.

### FR-3: Parser-Plugin-Architektur
- Jeder Provider-Parser ist ein eigenes Modul unter `src/moveon/parsers/<provider>.py` mit gemeinsamem Interface (abstrakte Basisklasse `BaseParser` mit `detect(path) -> bool` und `parse(path) -> Iterator[Message]`).
- Given ein neues Parser-Modul, das `BaseParser` implementiert und registriert ist, When `moveon extract <neuer-provider> file.zip`, Then funktioniert der Ablauf ohne Änderung am CLI-Code.

### FR-4: Guide Mode
- Given `moveon guide openai`, Then gibt das CLI die Schritt-für-Schritt-Anleitung zum Beantragen des Exports aus (Settings-Pfad, erwartete Wartezeit, erwarteter Dateiname). Analog für `anthropic`.

### FR-5: Erase-Generator
- Given `moveon erase openai --lang de`, Then existiert `MOVEON.d/erase/openai-erasure-de.md` mit: Anrede an den Datenschutzbeauftragten, Berufung auf Art. 17 DSGVO, Aufforderung zur Bestätigung binnen eines Monats (Art. 12 Abs. 3 DSGVO), Platzhalter `{{ACCOUNT_EMAIL}}` und `{{DATE}}`, sowie dem korrekten Einreichungskanal des Anbieters als Kommentar am Dateianfang.
- Given `moveon erase --all`, Then werden Anträge für alle im Manifest vorhandenen Provider in beiden Sprachen generiert plus `TRACKING.md` mit Checkliste: Antrag gestellt am / Frist (Datum + 1 Monat) / Antwort erhalten / Eskalation an zuständige Datenschutzbehörde.
- Given kein Export im Manifest für einen Provider, When `moveon erase <provider>`, Then Warnung "Export verifizieren vor Löschung empfohlen" — Antrag wird trotzdem generiert (Exit-Code 0).
- Jede generierte Datei enthält den Disclaimer: "Kein Rechtsrat. Vorlage vor Verwendung prüfen."

### FR-6: Manifest & Integrität
- `manifest.json` enthält pro Quelle: provider, Quelldateiname, SHA-256, Extraktionszeitpunkt, Nachrichtenzahl, Toolversion.
- Given ein zweiter `extract`-Lauf für denselben Provider, Then wird der alte `raw/`-Stand nicht stillschweigend überschrieben: CLI fragt nach Bestätigung (`--force` überspringt die Frage) und das Manifest behält die Historie beider Läufe.

### FR-7: Privacy Guarantees
- Given ein beliebiger CLI-Befehl, Then erfolgt kein ausgehender Netzwerkzugriff (verifizierbar: Testsuite enthält einen Test, der Socket-Zugriffe während extract/erase blockiert und Fehlschlag erwartet, falls doch einer stattfindet).

## Non-Goals (v0.1 — NICHT bauen)

- Kein Distill (Identitätssynthese, LLM-Aufrufe, Ollama) — das ist v0.2 mit eigenem PRD
- Kein Deploy (Modell-Setup, Memory-Layer-Integration) — v1.0
- Keine weiteren Provider als openai + anthropic (Plugin-Interface reicht)
- Keine GUI, kein Web-Interface, kein Dashboard
- Kein automatischer Versand von Löschanträgen, keine Anbieter-Logins, kein Browser-Automation
- Keine Telemetrie, keine Update-Checks

## Completion Checklist (deterministisch prüfbar)

- [ ] `pip install -e .` läuft fehlerfrei (Exit 0)
- [ ] `moveon --help` zeigt die 5 Befehle extract, guide, erase, status und die Version
- [ ] `pytest` läuft grün; Testabdeckung umfasst: beide Parser gegen synthetische Fixtures, korrupte ZIP (FR-1 Fehlerfall), Branch-Handling (FR-1), Erase-Templates beide Sprachen (FR-5), Doppel-Extract-Schutz (FR-6), Netzwerk-Blockade-Test (FR-7)
- [ ] `tests/fixtures/` enthält synthetische Beispiel-Exporte für beide Provider (je ≥3 Konversationen, davon ≥1 mit Branches beim OpenAI-Fixture, ≥1 mit Nicht-Text-Inhalt)
- [ ] End-to-End: `moveon extract openai tests/fixtures/openai-sample.zip && moveon extract anthropic tests/fixtures/anthropic-sample.zip && moveon erase --all && moveon status` läuft mit Exit 0 und erzeugt die komplette Bundle-Struktur wie oben spezifiziert
- [ ] `README.md` (liegt bei), `LICENSE` (MIT), `CONTRIBUTING.md` (kurz: Parser-Plugins als Einstieg) existieren im Repo-Root
- [ ] `ruff check .` läuft ohne Fehler (ruff als Dev-Dependency)
- [ ] Kein Import von `requests`, `httpx`, `urllib.request` o. ä. im Laufzeitcode (grep-prüfbar)

## Hinweise für den Build

- Die realen Exportformate von OpenAI/Anthropic können sich ändern. Parser defensiv bauen: unbekannte Felder ignorieren, fehlende Felder mit Warnung überspringen, nie crashen wegen Zusatzfeldern.
- Fixtures sind aus öffentlich dokumentierten Formatbeschreibungen zu synthetisieren, nicht aus echten Exports.
- DSGVO-Templates: sachlich-formeller Ton, keine Drohungen, Standardformulierungen deutscher Musterschreiben (Verbraucherzentrale-Stil).
- Menschliche Prüfung nach dem Build: Templates fachlich gegenlesen (macht der Mensch, nicht der Agent).
