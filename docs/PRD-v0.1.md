# PRD: Move On v0.1 — Extract + Erase

<!-- Loki-Mode-optimiert: messbare Ziele, FR-Format, Given/When/Then, deterministische Completion-Checkliste. -->
<!-- Scope: NUR v0.1 (Extract + Erase). Distill (v0.2) und Deploy (v1.0) sind explizit AUSGESCHLOSSEN. -->

## Product Summary

Move On ist ein Python-CLI-Tool, das offizielle Datenexporte proprietärer KI-Anbieter (OpenAI/ChatGPT, Anthropic/Claude) in ein offenes, anbieterneutrales Format normalisiert und versandfertige DSGVO-Löschanträge (Art. 17) generiert. Kein Netzwerkzugriff, keine Telemetrie, keine Anbieter-Logins.

**Elevator pitch:** "Hol deine Daten. Lösch dich raus."

**Warum Extract + Erase ohne Distill ein vollständiger Wedge ist:** Move On ist kein Format-Konverter. Es ist ein Completion-System gegen Trägheit. Die extrahierten JSONL-Dateien sind keine Rohdaten für spätere Analyse — sie sind Evidenz: überprüfbare Beweise, dass ein Export stattgefunden hat, wie viele Konversationen enthalten waren, und ob der Anbieter vollständig geliefert hat. Der Löschantrag verweist auf diese Evidenz. Zusammen verwandeln Extract + Erase "ich sollte mal meine Daten holen" in "ich habe es getan und kann es beweisen." Das Gehen ist der Punkt, nicht das Ankommen.

## Tech Stack (verbindlich)

- Python ≥3.11, Paketstruktur `src/moveon/`, Packaging via `pyproject.toml` (hatchling)
- CLI-Framework: Typer
- Datenmodelle: Pydantic v2
- Templates: `string.Template` (stdlib) für Erase-Vorlagen mit Benutzer-Platzhaltern
- Tests: pytest, Testdaten als Fixtures in `tests/fixtures/` (synthetische Beispiel-Exporte, KEINE echten Nutzerdaten)
- Ausgabeformat: JSONL im Move On Conversation Format v1 (Schema siehe unten, Provenienz in `metadata`-Feldern)
- Encoding: UTF-8 für alle Ein- und Ausgaben
- Lizenz: MIT (`LICENSE`-Datei im Repo-Root)
- Keine externen API-Calls, keine Telemetrie, keine Netzwerkzugriffe zur Laufzeit

## CLI-Oberfläche (verbindlich)

```
moveon extract <provider> <export.zip> [--out DIR] [--force] [--verbose]   # provider: openai | anthropic
moveon guide [provider]                              # ohne Argument: listet Provider; mit Argument: Exportanleitung
moveon erase <provider> [--lang de|en] [--out DIR]   # generiert Löschantrag
moveon erase --all [--lang de|en]
moveon status [--json]                               # zeigt Manifest-Inhalt; --json für maschinenlesbare Ausgabe
moveon --version                                     # gibt Toolversion aus (aus pyproject.toml)
```

`--out DIR` bestimmt das Elternverzeichnis des Bundles: `--out /tmp` erzeugt `/tmp/MOVEON.d/`. Default: `./MOVEON.d/`.

`--verbose` gibt zusätzliche Informationen während der Verarbeitung aus (Konversationszahl, übersprungene Felder, Branches).

Exit-Codes: `0` = Erfolg, `1` = Fehler. Bei Erfolg gibt das CLI eine einzeilige Zusammenfassung aus (z. B. "Extracted 56 conversations (1234 messages) from openai export."). Bei Fehlern nennt die Meldung Datei, Grund und nächsten Schritt.

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

Schema `messages.jsonl` — Move On Conversation Format v1 (eine Zeile pro Konversation):
```json
{"format_version": "1", "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}], "metadata": {"source": "openai", "conversation_id": "...", "conversation_title": "...", "created_at": "ISO-8601", "updated_at": "ISO-8601"}}
```

SHA-256-Hash in `manifest.json` bezieht sich auf die Quell-ZIP-Datei (Input-Integrität), nicht auf die erzeugte JSONL.

## Functional Requirements

### FR-1: Extract OpenAI
Parst das offizielle ChatGPT-Datenexport-ZIP (enthält `conversations.json`).

- Given ein valides ChatGPT-Export-ZIP, When `moveon extract openai export.zip`, Then existiert `MOVEON.d/raw/openai/messages.jsonl` mit einer JSONL-Zeile pro Konversation (jede Zeile enthält alle Nachrichten der Konversation als Array) und ein Eintrag in `manifest.json` mit SHA-256 des Quell-ZIPs.
- Given ein Export mit verschachtelten Konversationsbäumen (ChatGPT-`mapping`-Struktur mit Branches), When extract läuft, Then wird der aktive Pfad extrahiert; verworfene Branches werden gezählt und im CLI-Output als Zahl ausgewiesen. **Branch-Walking-Algorithmus:** `conversations.json` enthält pro Konversation ein `mapping`-Dict (Node-ID → Node-Objekt mit `parent`, `children`, `message`). Der aktive Pfad wird durch Rückwärtslaufen von `current_node` über `parent`-Pointer bis zur Wurzel (Node ohne `parent`) ermittelt. Jeder Node auf diesem Pfad liefert eine Message; Nodes außerhalb des Pfads sind verworfene Branches.
- Given eine korrupte oder nicht als ChatGPT-Export erkennbare ZIP, When extract läuft, Then Exit-Code 1 und eine Fehlermeldung, die Datei und Grund benennt; `MOVEON.d/` bleibt unverändert.
- Given ein Export mit Nicht-Text-Inhalten, When extract läuft, Then werden diese als `{"content": "[non-text content: <type>]"}` platzhalter-kodiert statt das Parsing abzubrechen. Bekannte Typen: `image` (DALL-E, Uploads), `audio` (Voice-Mode), `code_output` (Code-Interpreter), `file` (Datei-Uploads), `tool_use` (Plugin/Tool-Aufrufe), `thinking` (Reasoning-Blöcke bei Claude). Unbekannte Typen: `unknown`.

### FR-2: Extract Anthropic
Parst das offizielle Claude-Datenexport-Archiv (conversations.json-Struktur des Claude-Exports).

- Given ein valides Claude-Export-Archiv, When `moveon extract anthropic export.zip`, Then existiert `MOVEON.d/raw/anthropic/messages.jsonl` analog FR-1.
- Given beide Provider wurden extrahiert, When `moveon status`, Then listet die Ausgabe beide Quellen mit Exportdatum, Nachrichtenzahl und Hash.

### FR-3: Parser-Plugin-Architektur
- Jeder Provider-Parser ist ein eigenes Modul unter `src/moveon/parsers/<provider>.py` mit gemeinsamem Interface: abstrakte Basisklasse `BaseParser` mit `validate(path) -> bool` (prüft ob die Datei zum Provider passt) und `parse(path) -> Iterator[Conversation]`.
- Parser-Registrierung: Dict-basierte Registry in `src/moveon/parsers/__init__.py` (`REGISTRY: dict[str, type[BaseParser]]`).
- Given ein neues Parser-Modul, das `BaseParser` implementiert und in `REGISTRY` eingetragen ist, When `moveon extract <neuer-provider> file.zip`, Then funktioniert der Ablauf ohne Änderung am CLI-Code.

### FR-4: Guide Mode
- Given `moveon guide openai`, Then gibt das CLI die Schritt-für-Schritt-Anleitung zum Beantragen des Exports aus (Settings-Pfad, erwartete Wartezeit, erwarteter Dateiname). Analog für `anthropic`.

### FR-5: Erase-Generator
- Given `moveon erase openai --lang de`, Then existiert `MOVEON.d/erase/openai-erasure-de.md` mit: Anrede an den Datenschutzbeauftragten, Berufung auf Art. 17 DSGVO, Aufforderung zur Bestätigung binnen eines Monats (Art. 12 Abs. 3 DSGVO), Platzhalter `$ACCOUNT_EMAIL` und `$DATE` (via `string.Template`, Benutzer füllt vor Versand aus), sowie dem Einreichungskanal des Anbieters als Kommentar am Dateianfang.
- Einreichungskanäle (im Template als Kommentar, Mensch verifiziert vor Release):
  - OpenAI: https://privacy.openai.com/policies (Privacy Portal, DSAR-Formular)
  - Anthropic: privacy@anthropic.com (E-Mail an Datenschutzteam)
- Given `moveon erase --all`, Then werden Anträge für alle im Manifest vorhandenen Provider in beiden Sprachen generiert plus `TRACKING.md` mit Checkliste: Antrag gestellt am `___` / Frist (nach Versand selbst eintragen: Versanddatum + 1 Monat gem. Art. 12 Abs. 3 DSGVO, Frist läuft ab Zugang beim Verantwortlichen) / Antwort erhalten / Eskalation an zuständige Datenschutzbehörde.
- Given kein Export im Manifest für einen Provider, When `moveon erase <provider>`, Then Warnung "Export verifizieren vor Löschung empfohlen" — Antrag wird trotzdem generiert (Exit-Code 0).
- Jede generierte Datei enthält den Disclaimer: "Kein Rechtsrat. Vorlage vor Verwendung prüfen. Löschungsrecht nach Art. 17 DSGVO kann nach Art. 17 Abs. 3 eingeschränkt sein (z. B. Aufbewahrungspflichten). Im Zweifelsfall Datenschutzbehörde oder Rechtsberatung konsultieren."

### FR-6: Manifest & Integrität
- `manifest.json` enthält pro Provider ein `runs[]`-Array. Jeder Eintrag in `runs[]` enthält: provider, Quelldateiname, SHA-256, Extraktionszeitpunkt, Nachrichtenzahl, Konversationszahl, Toolversion. Schema:
```json
{
  "version": "1",
  "providers": {
    "openai": {
      "runs": [
        {"source_file": "export.zip", "sha256": "...", "extracted_at": "ISO-8601", "message_count": 1234, "conversation_count": 56, "tool_version": "0.1.0"}
      ],
      "active_run": 0
    }
  }
}
```
- Given ein zweiter `extract`-Lauf für denselben Provider, Then wird der alte `raw/`-Stand nicht stillschweigend überschrieben: CLI fragt nach Bestätigung (`--force` überspringt die Frage). Der neue Run wird an `runs[]` angehängt, `active_run` zeigt auf den neuen Index. Die bisherige `raw/<provider>/messages.jsonl` wird als `raw/<provider>/messages-run-N.jsonl` archiviert (N = vorheriger Run-Index), bevor die neue Datei geschrieben wird.
- Given kein TTY (z. B. Pipe oder Skript) und kein `--force`, When `moveon extract` auf einen bestehenden Provider trifft, Then Exit-Code 1 mit Fehlermeldung "Use --force to overwrite existing extraction (non-interactive mode)."

### FR-7: Privacy Guarantees
- Given ein beliebiger CLI-Befehl, Then erfolgt kein ausgehender Netzwerkzugriff (verifizierbar: Testsuite enthält einen Test, der Socket-Zugriffe während extract/erase blockiert und Fehlschlag erwartet, falls doch einer stattfindet).

### FR-8: Data Protection (CSO-Review)

**Kontext:** `MOVEON.d/raw/` enthält den kompletten KI-Chatverlauf im Klartext — potenziell persönliche Gedanken, Gesundheitsdaten, Geschäftsgeheimnisse, Code mit Zugangsdaten. Ein versehentlicher `git commit` oder Cloud-Sync exponiert alles unwiderruflich. Das Privacy-Versprechen des Tools muss sich auf die eigenen Outputs erstrecken.

- **Dateiberechtigungen:** `MOVEON.d/` und alle Unterverzeichnisse werden mit `0700` erstellt (nur Owner-Zugriff). Dateien innerhalb des Bundles mit `0600`. Build-Hint: `os.makedirs(path, mode=0o700, exist_ok=True)`.
- **Git-Schutz:** Bei jeder Schreiboperation in `MOVEON.d/` prüft das Tool, ob eine Datei `MOVEON.d/.gitignore` existiert. Falls nicht, wird sie mit Inhalt `*` erzeugt (verhindert versehentliches `git add` des Bundles).
- **Git-Warnung:** Given `MOVEON.d/` liegt in einem Git-Repo (erkennbar via `git rev-parse --show-toplevel` vom Bundle-Pfad aus), When `MOVEON.d/` nicht in der `.gitignore` des Repos steht, Then gibt das CLI nach jeder Schreiboperation eine Warnung aus: `Warning: MOVEON.d/ is inside a git repo but not in .gitignore. Your chat history could be accidentally committed.`
- **Erfolgswarnung:** Nach erfolgreicher Extraktion gibt das CLI zusätzlich zur Statistik-Zeile eine Warnung aus: `⚠ MOVEON.d/raw/ contains your chat history in plaintext. Do not commit to git or store in cloud-synced folders.`
- **Output-Integrität (optional):** `manifest.json` kann pro Run zusätzlich einen SHA-256-Hash der erzeugten JSONL-Datei enthalten (`output_sha256`). `moveon status` prüft dann, ob die JSONL unverändert ist, und meldet Abweichungen. Stärkt die Evidenzkette ("überprüfbare Beweise"), ist aber kein Blocker für die Completion Checklist.

## Non-Goals (v0.1 — NICHT bauen)

- Kein Distill (Identitätssynthese, LLM-Aufrufe, Ollama) — das ist v0.2 mit eigenem PRD
- Kein Deploy (Modell-Setup, Memory-Layer-Integration) — v1.0
- Keine weiteren Provider als openai + anthropic (Plugin-Interface reicht)
- Keine GUI, kein Web-Interface, kein Dashboard
- Kein automatischer Versand von Löschanträgen, keine Anbieter-Logins, kein Browser-Automation
- Keine Telemetrie, keine Update-Checks

## Completion Checklist (deterministisch prüfbar)

- [ ] `pip install -e .` läuft fehlerfrei (Exit 0)
- [ ] `moveon --help` zeigt die 4 Befehle extract, guide, erase, status; `moveon --version` gibt die Versionsnummer aus
- [ ] `pytest` läuft grün; Testabdeckung umfasst: beide Parser gegen synthetische Fixtures, korrupte ZIP (FR-1 Fehlerfall), Branch-Handling (FR-1), Erase-Templates beide Sprachen (FR-5), Doppel-Extract-Schutz (FR-6), Netzwerk-Blockade-Test (FR-7)
- [ ] `tests/fixtures/` enthält synthetische Beispiel-Exporte für beide Provider (je ≥3 Konversationen, davon ≥1 mit Branches beim OpenAI-Fixture, ≥1 mit Nicht-Text-Inhalt)
- [ ] End-to-End: `moveon extract openai tests/fixtures/openai-sample.zip && moveon extract anthropic tests/fixtures/anthropic-sample.zip && moveon erase --all && moveon status` läuft mit Exit 0 und erzeugt die komplette Bundle-Struktur wie oben spezifiziert
- [ ] `README.md` (liegt bei), `LICENSE` (MIT), `CONTRIBUTING.md` (kurz: Parser-Plugins als Einstieg) existieren im Repo-Root
- [ ] `ruff check .` läuft ohne Fehler (ruff als Dev-Dependency)
- [ ] Kein Import von `requests`, `httpx`, `urllib.request` o. ä. im Laufzeitcode (grep-prüfbar)
- [ ] `MOVEON.d/` steht in `.gitignore` des Repos; nach `moveon extract` existiert `MOVEON.d/.gitignore` mit Inhalt `*`
- [ ] `MOVEON.d/` wird mit Dateiberechtigungen `0700` erstellt; Dateien darin mit `0600` (verifizierbar via `stat`)

## Hinweise für den Build

### Modulstruktur (verbindlich)

```
src/moveon/
├── __init__.py              # Version aus pyproject.toml lesen
├── cli.py                   # Typer-App, alle Commands
├── models.py                # Pydantic-Modelle: Conversation, Message, Manifest
├── bundle.py                # MOVEON.d/ lesen/schreiben, Manifest-Logik
├── erase.py                 # Template-Rendering (string.Template), TRACKING.md
├── guide.py                 # Exportanleitungen pro Provider
├── exceptions.py            # MoveonError (Basis), ParseError, BundleError, ManifestError
├── parsers/
│   ├── __init__.py          # REGISTRY: dict[str, type[BaseParser]], get_parser()
│   ├── base.py              # BaseParser (ABC): validate(), parse()
│   ├── openai.py            # OpenAI/ChatGPT-Parser
│   └── anthropic.py         # Anthropic/Claude-Parser
└── templates/
    ├── openai-erasure-de.txt
    ├── openai-erasure-en.txt
    ├── anthropic-erasure-de.txt
    ├── anthropic-erasure-en.txt
    └── tracking.txt
```

### Implementierungsreihenfolge (empfohlen)

1. `models.py` — Pydantic-Modelle (Conversation, Message, Metadata)
2. `parsers/base.py` + `parsers/openai.py` — BaseParser-ABC + erster Parser
3. `bundle.py` + `models.py` (Manifest) — MOVEON.d/-Struktur, Manifest lesen/schreiben
4. `cli.py` — Typer-Commands (`extract`, `status`)
5. `erase.py` + `guide.py` — Templates und Anleitungen
6. `parsers/anthropic.py` — zweiter Parser
7. Tests durchgehend, finaler Durchlauf Completion Checklist

### Parser-Richtlinien

- Die realen Exportformate von OpenAI/Anthropic können sich ändern. Parser defensiv bauen: unbekannte Felder ignorieren, fehlende Felder mit Warnung überspringen, nie crashen wegen Zusatzfeldern.
- Fixtures sind aus öffentlich dokumentierten Formatbeschreibungen zu synthetisieren, nicht aus echten Exports.
- Bei Fehlern in einzelnen Konversationen: Warnung ausgeben, Konversation überspringen, restliche Konversationen weiter verarbeiten. Exit-Code bleibt 0, CLI gibt Zusammenfassung mit Zahl der übersprungenen Konversationen aus.

### Ressourcen-Constraints

- Peak-RAM darf 2× Dateigröße der Eingabe-ZIP nicht überschreiten. Für große `conversations.json` (dreistellig MB): streaming/iteratives Parsen statt vollständiges Einlesen.
- ZIP-Sicherheit: Vor dem Entpacken prüfen auf Path-Traversal (`../` in Pfaden), Zip-Bombs (unkomprimierte Gesamtgröße > 10 GB → Abbruch), verschlüsselte Archive (→ Exit 1 mit Hinweis).
- Atomizität: Neue Dateien in temporäres Verzeichnis schreiben, dann per `os.rename()` / `shutil.move()` an Zielort verschieben. Bei Abbruch bleibt der alte Stand intakt.

### Exception-Hierarchie

```
MoveonError (Basis — alle Tool-Exceptions erben davon)
├── ParseError        # Fehler beim Parsen eines Exports
├── BundleError       # Fehler beim Lesen/Schreiben des Bundles
└── ManifestError     # Manifest korrupt oder inkompatibel
```

### Teststruktur

```
tests/
├── conftest.py              # Gemeinsame Fixtures, Pfad-Helfer
├── fixtures/
│   ├── openai-sample.zip    # Synthetischer OpenAI-Export (≥3 Konversationen, Branches, Non-Text)
│   └── anthropic-sample.zip # Synthetischer Anthropic-Export (≥3 Konversationen, Non-Text)
├── test_parsers/
│   ├── test_openai.py
│   └── test_anthropic.py
├── test_bundle.py
├── test_erase.py
├── test_cli.py              # CLI-Integration via CliRunner
└── test_network_block.py    # Socket-Blockade-Test (FR-7)
```

- Socket-Blockade-Test (FR-7): Blockiert auf Python-Ebene via `socket.socket`-Monkey-Patch. Dokumentierter Scope: verifiziert, dass der moveon-Laufzeitcode selbst keine Sockets öffnet. Erkennt keine Netzwerkzugriffe, die über Subprozesse oder C-Extensions laufen.

### DSGVO-Templates

- Sachlich-formeller Ton, keine Drohungen, Standardformulierungen deutscher Musterschreiben (Verbraucherzentrale-Stil).
- Menschliche Prüfung nach dem Build: Templates fachlich gegenlesen (macht der Mensch, nicht der Agent).

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | RESOLVED | 8 tasks (6×P1, 2×P2), alle ins PRD eingearbeitet. Provider-Scope: 2 (OpenAI + Anthropic). |
| Codex Review | `/codex review` | Independent 2nd opinion | 1 | RESOLVED | "Right to Exit"-Framing, Completion-System-Konzept, CLI-Premise-Challenge (v0.2-relevant). |
| Eng Review | `/plan-eng-review` | Architecture & tests | 1 | RESOLVED | 20 Findings (10 Tasks), alle eingearbeitet: string.Template, dict-Registry, Branch-Walking, ZIP-Security, Atomizität, Exception-Hierarchie, Socket-Test-Scope. |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | SKIPPED | Kein UI-Scope in v0.1. |
| DX Review | `/plan-devex-review` | Developer experience | 1 | RESOLVED | 3 Tasks: Modulstruktur, Implementierungsreihenfolge, Teststruktur — alle als Build Hints eingearbeitet. |
| CSO Review | `/cso` | Security & Privacy | 1 | RESOLVED | 5 Findings (1×CRITICAL, 3×HIGH, 1×MEDIUM): .gitignore, Dateiberechtigungen, User-Warnung, Output-Integrität. Alle als FR-8 eingearbeitet. |

**VERDICT:** ALLE REVIEWS INKL. CSO ABGESCHLOSSEN. PRD ist build-ready für Loki-Mode.

NO UNRESOLVED DECISIONS
