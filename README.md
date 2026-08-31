# Move On

[![PyPI](https://img.shields.io/pypi/v/moveon)](https://pypi.org/project/moveon/)
[![Python](https://img.shields.io/pypi/pyversions/moveon)](https://pypi.org/project/moveon/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/ur-grue/move-on/actions/workflows/ci.yml/badge.svg)](https://github.com/ur-grue/move-on/actions/workflows/ci.yml)

**Extract your AI data. Request deletion. Move on.**

Move On parses your AI chat exports into a portable format, generates ready-to-send GDPR erasure requests, tracks deadlines, and escalates to data protection authorities when providers don't respond.

No network access. No telemetry. No provider logins.

## Quick Start

```bash
pip install moveon
```

```bash
# 1. See how to export your data
moveon guide openai

# 2. Parse and normalize the export
moveon extract openai ~/Downloads/export.zip

# 3. Generate erasure requests (Art. 17 GDPR)
moveon erase --all

# 4. Track when you sent the request
moveon track openai --sent 2026-08-01

# 5. Check deadlines and status
moveon status

# 6. File a DPA complaint if overdue (Art. 77 GDPR)
moveon escalate openai
```

## Supported Providers

| Provider | Extract | Erase | Track | Escalate |
|---|---|---|---|---|
| OpenAI (ChatGPT) | ✓ | ✓ | ✓ | ✓ |
| Anthropic (Claude) | ✓ | ✓ | ✓ | ✓ |
| Google (Gemini) | ✓ | ✓ | ✓ | ✓ |
| Meta (Meta AI) | ✓ | ✓ | ✓ | ✓ |
| xAI (Grok) | ✓ | ✓ | ✓ | ✓ |
| Mistral (Le Chat) | ✓ | ✓ | ✓ | ✓ |
| Perplexity | ✓ | ✓ | ✓ | ✓ |

## What It Does

**Extract** parses the provider's export ZIP and normalizes conversations into JSONL — one portable format for all providers.

**Erase** generates pre-written GDPR Art. 17 erasure requests in German and English, ready to send.

**Track** records when you sent the request and calculates the Art. 12(3) deadline (one calendar month).

**Diff** compares two extraction runs to show what changed between exports.

**Status** shows deadlines, overdue requests, and next steps.

**Escalate** generates a complete Art. 77 complaint to the responsible DPA, with evidence chain, SHA-256 hashes, and deadline proof. Opens your mail client or prints the complaint text.

Everything stays in `MOVEON.d/` — a local bundle that never touches the network.

## Evidence Chain

Every extraction run is SHA-256 hashed and chained to the previous run. If a provider claims your data was already deleted, the evidence chain proves what existed and when. `moveon status` verifies chain integrity automatically.

## DPA Database

Move On includes a database of 31 data protection authorities (27 EU + 3 EEA + UK) with contact details, complaint URLs, and email addresses. It routes complaints based on the provider's EU establishment (Art. 56 GDPR) or your residence (Art. 77 GDPR) via `--country`.

## Installation

### pip

```bash
pip install moveon
```

### Homebrew

```bash
brew install ur-grue/tap/moveon
```

### From source

```bash
git clone https://github.com/ur-grue/move-on.git
cd move-on
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Security

- **Zero network access** at runtime — verified by socket-blocking tests in CI
- `MOVEON.d/` created with restrictive permissions (0700 directory, 0600 files)
- Automatic `.gitignore` prevents accidental commits of personal data
- Two dependencies only (typer, pydantic) — fully auditable
- No telemetry, no analytics, no phone-home

## Shell Completion

```bash
# bash
moveon --install-completion bash

# zsh
moveon --install-completion zsh

# fish
moveon --install-completion fish
```

## License

MIT
