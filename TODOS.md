# TODOS

## v0.2

- [x] **Google Takeout .tgz-Support** — Google Takeout erzeugt auch .tgz-Archive, nicht nur ZIP. Der aktuelle CLI-Code (`_check_zip_security()`, Parser `validate()`) akzeptiert ausschließlich ZIP. Prüfen, ob .tgz für Gemini-Exporte relevant ist, und ggf. `tarfile`-Support ergänzen (stdlib, kein neues Dependency).
  - **Surfaced by:** Codex Outside Voice (plan-eng-review, 2026-08-11)
  - **Status:** Deferred — ZIP ist der empfohlene Standardpfad. .tgz-Support in v0.5 bei Bedarf.

## v0.3

- [x] **conversation_id-Stabilität im Parser-Vertrag** — Docstring in `BaseParser.parse()` dokumentiert jetzt die Anforderung.
