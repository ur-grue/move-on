# Changelog

## Unreleased

- Consistent English CLI output and export guides (letter templates remain de/en)
- `erase` and `escalate` default to `--lang en`; use `--lang de` for German letters
- Corrupt or invalid export archives report a one-line error instead of a traceback
- Tracebacks no longer print local variables (they can contain chat content)
- `MOVEON.d/raw/` is created with 0700 like the rest of the bundle
- CI: ruff format check, ruff >= 0.13, mypy pinned in the dev extra
- Release workflow: tag `v*` builds, publishes to PyPI via trusted publishing, and creates a GitHub release
- Removed internal planning documents from the repository

## 1.0.0 — 2026-08-13

- `moveon escalate` generates Art. 77 GDPR complaints to responsible DPAs
- Three escalation paths: mailto (zero-network), stdout fallback, SMTP (`--send`)
- Complaint text includes evidence chain, SHA-256 hashes, and deadline proof
- Lazy imports for faster CLI startup (~120ms for --help/--version)
- Full type checking (mypy strict), linting (ruff), 223 tests

## 0.7.0 — 2026-08-12

- `moveon track` records erasure request dates and calculates Art. 12(3) deadlines
- DPA database with 31 authorities (27 EU + 3 EEA + UK)
- `moveon status` shows deadlines, overdue requests, escalation guidance
- `--country` flag for Art. 77 DPA routing by residence
- ErasureStatus enum: pending, sent, overdue, complaint_filed

## 0.5.0 — 2026-08-11

- xAI/Grok, Mistral/Le Chat, Perplexity parsers
- Erasure templates (de/en) for all 7 providers
- Export guides for all providers
- Homebrew formula

## 0.3.0 — 2026-08-11

- `moveon diff` compares extraction runs
- Evidence chain with SHA-256 hash linking
- Shell completion (bash, zsh, fish)

## 0.1.0 — 2026-08-10

- Initial release
- OpenAI, Anthropic, Google, Meta parsers
- `moveon extract`, `moveon guide`, `moveon erase`, `moveon status`
- GDPR Art. 17 erasure request generation (de/en)
- MOVEON.d/ bundle with manifest and .gitignore
