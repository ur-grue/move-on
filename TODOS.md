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
