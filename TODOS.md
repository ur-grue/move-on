# TODOS

## v0.2

- [ ] **Google Takeout .tgz-Support** — Google Takeout erzeugt auch .tgz-Archive, nicht nur ZIP. Der aktuelle CLI-Code (`_check_zip_security()`, Parser `validate()`) akzeptiert ausschließlich ZIP. Prüfen, ob .tgz für Gemini-Exporte relevant ist, und ggf. `tarfile`-Support ergänzen (stdlib, kein neues Dependency).
  - **Surfaced by:** Codex Outside Voice (plan-eng-review, 2026-08-11)
  - **Depends on:** Google Gemini Parser (v0.2)

## v0.3

- [ ] **conversation_id-Stabilität im Parser-Vertrag** — `moveon diff` setzt stabile, eindeutige `conversation_id`s pro Provider-Export voraus. `BaseParser` ABC dokumentiert das nicht. Docstring oder Abstract-Property ergänzen, die klarstellt: `metadata.conversation_id` muss über Exporte hinweg stabil und eindeutig sein.
  - **Surfaced by:** Codex Outside Voice (plan-eng-review, 2026-08-11)
  - **Depends on:** moveon diff Implementation (v0.3)
