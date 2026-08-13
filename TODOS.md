# TODOS

## v0.2

- [x] **Google Takeout .tgz-Support** — Google Takeout erzeugt auch .tgz-Archive, nicht nur ZIP. Der aktuelle CLI-Code (`_check_zip_security()`, Parser `validate()`) akzeptiert ausschließlich ZIP. Prüfen, ob .tgz für Gemini-Exporte relevant ist, und ggf. `tarfile`-Support ergänzen (stdlib, kein neues Dependency).
  - **Surfaced by:** Codex Outside Voice (plan-eng-review, 2026-08-11)
  - **Status:** Deferred — ZIP ist der empfohlene Standardpfad. .tgz-Support in v0.5 bei Bedarf.

## v0.3

- [x] **conversation_id-Stabilität im Parser-Vertrag** — Docstring in `BaseParser.parse()` dokumentiert jetzt die Anforderung.

## v0.5

- [x] **xAI/Grok Parser** — ZIP mit `prod-grok-backend.json`. Sender-Normalisierung (human/assistant/ASSISTANT/model-name). ISO 8601 Timestamps auf Conversation-Ebene.
- [x] **Mistral/Le Chat Parser** — ZIP mit `chat-{uuid}.json` pro Konversation. Flat Message-Array mit `contentChunks`-Support. Titel aus erster User-Nachricht.
- [x] **Perplexity Parser** — ZIP mit `threads.json`. Steps-Array (query_str/final_response) statt Message-Array. Slug als conversation_id.
- [x] **Erasure Templates** — 6 neue Templates (de/en) für xai, mistral, perplexity mit provider-spezifischen Einreichungskanälen.
- [x] **Export Guides** — Anleitungen für alle drei neuen Provider.
- [x] **Homebrew Formula** — `homebrew/moveon.rb` als Vorlage für `ur-grue/homebrew-tap`. SHA256 muss nach Release ersetzt werden.
- [ ] **Homebrew Tap publizieren** — GitHub-Repo `ur-grue/homebrew-tap` erstellen, Formula einchecken, `brew install ur-grue/tap/moveon` testen.

## v0.7

- [x] **ErasureStatus Enum** — `pending | sent | overdue | complaint_filed` auf `ProviderManifest`. Nicht in `HASH_FIELDS`.
- [x] **Fristberechnung** — Art. 12 Abs. 3 DSGVO: Zugang + 1 Kalendermonat. `calendar.monthrange()` aus stdlib, kein `dateutil`.
- [x] **DPA-Datenbank** — `src/moveon/data/dpa.json` mit 31 Behörden (27 EU + 3 EEA + UK). Quellen: EDPB, datenanfragen.de (CC BY 4.0).
- [x] **`moveon track`** — Versenddatum setzen, Frist berechnen, DPA anzeigen, TRACKING.md regenerieren.
- [x] **`moveon status` erweitert** — Zeigt Fristen, Überfälligkeit, Eskalationsempfehlung.
- [x] **`--country` Flag** — Art. 77 DSGVO: DPA-Routing nach Wohnsitz statt Provider-Jurisdiktion.
- [x] **Provider-Jurisdiktionen** — Mapping aller 7 Provider auf EU-Niederlassung (IE für OpenAI/Anthropic/Google/Meta/xAI/Perplexity, FR für Mistral).

## v1.0

- [x] **`moveon escalate`** — Generiert vorausgefüllte Art.-77-Beschwerde an zuständige DPA.
- [x] **Drei Eskalationspfade** — (1) `webbrowser.open("mailto:...")` zero-network, (2) stdout-Fallback, (3) `--send` via `smtplib` mit interaktiver Bestätigung.
- [x] **Beschwerdetext de/en** — Enthält Evidence Chain, SHA-256, Fristnachweis, Provider-Kontakte.
- [x] **Socket-Blocking-Tests** — Netzwerkblockade für `track` und `escalate` (mailto-Pfad). SMTP-Pfad (`--send`) explizit opt-in.
- [x] **223 Tests bestanden** — 167 (v0.5) + 24 (tracking) + 14 (DPA) + 16 (escalate) + 2 (network).

## Offen

- [ ] **Homebrew Tap publizieren** — GitHub-Repo `ur-grue/homebrew-tap` erstellen, Formula einchecken, SHA256 aktualisieren.
- [ ] **Homebrew Formula auf v1.0.0 aktualisieren** — URL und SHA256 in `homebrew/moveon.rb` nach Tag.
