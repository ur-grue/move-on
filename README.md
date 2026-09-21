# Move On

[![PyPI](https://img.shields.io/pypi/v/moveon)](https://pypi.org/project/moveon/)
[![Python](https://img.shields.io/pypi/pyversions/moveon)](https://pypi.org/project/moveon/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/ur-grue/move-on/actions/workflows/ci.yml/badge.svg)](https://github.com/ur-grue/move-on/actions/workflows/ci.yml)

**Extract your AI chat history. Request deletion. Prove it. Move on.**

Move On turns the data export of an AI chat provider into one portable
format, writes the GDPR erasure request for you, tracks the legal
deadline, and drafts the complaint to the data protection authority if the
provider stays silent.

Runs entirely on your machine. No network access, no telemetry, no logins.

```
$ moveon extract openai ~/Downloads/chatgpt-export.zip
Extracted 312 conversations (4871 messages) from openai export.

$ moveon erase openai
Generated: MOVEON.d/erase/openai-erasure-en.md

$ moveon track openai --sent 2026-09-01
Tracked erasure request for openai:
  Sent:     2026-09-01
  Deadline: 2026-10-01 (Art. 12(3) GDPR)

  Supervisory authority: Data Protection Commission
  Complaint email:       info@dataprotection.ie

$ moveon status
  Provider: openai
  Conversations: 312
  Integrity: ✓ output unchanged
  Status: deadline running (10 day(s) left)
```

## Why

Deleting your account is one click. Getting your data *out* first, and
proving later what the provider held, is not. Most people never send the
erasure request, and of those who do, few follow up when the one-month
deadline passes.

Move On removes the friction at each step:

| Step | Without Move On | With Move On |
|---|---|---|
| Read the export | Dig through nested JSON, one schema per provider | One JSONL format for all seven providers |
| Write the request | Find the right article, the right address, the right wording | `moveon erase` — ready to send, cites Art. 17 GDPR |
| Remember the deadline | Calendar reminder, if you set one | `moveon status` — counts down, flags overdue |
| Escalate | Which authority? What evidence? | `moveon escalate` — routes to the right DPA, attaches SHA-256 evidence |

## Install

```bash
pip install moveon           # or: pipx install moveon
brew install ur-grue/tap/moveon
```

Python 3.11 or newer. Two dependencies: typer and pydantic.

## Supported providers

| Provider | Product | Export guide |
|---|---|---|
| OpenAI | ChatGPT | `moveon guide openai` |
| Anthropic | Claude | `moveon guide anthropic` |
| Google | Gemini | `moveon guide google` |
| Meta | Meta AI | `moveon guide meta` |
| xAI | Grok | `moveon guide xai` |
| Mistral | Le Chat | `moveon guide mistral` |
| Perplexity | Perplexity | `moveon guide perplexity` |

Extract, erase, track and escalate work for all of them. Missing one?
[Open a provider request](https://github.com/ur-grue/move-on/issues/new?template=provider_request.md)
or [add a parser](CONTRIBUTING.md) — it is about 120 lines.

## Workflow

1. **`moveon guide <provider>`** — where to click to request the export, and
   how long the provider takes to deliver it.
2. **`moveon extract <provider> export.zip`** — parses the archive and writes
   `MOVEON.d/raw/<provider>/messages.jsonl`. Every run is SHA-256 hashed and
   recorded in `MOVEON.d/manifest.json`.
3. **`moveon erase <provider>`** — writes an Art. 17 GDPR erasure request in
   English (`--lang de` for German) with the provider's submission channel.
   `--all` covers every provider at once.
4. **`moveon track <provider> --sent YYYY-MM-DD`** — records the send date
   and computes the Art. 12(3) deadline: one calendar month.
5. **`moveon status`** — deadlines, overdue requests, integrity of your
   extracted data, next step.
6. **`moveon escalate <provider>`** — once overdue, drafts an Art. 77
   complaint to the responsible authority and opens it in your mail client.
   `--country DE` routes to your home authority instead of the provider's.
   `--send` delivers via your own SMTP server; it is the only command that
   touches the network, and it asks first.

`moveon diff <provider>` compares two extraction runs, so you can check
what a provider actually deleted after a second export.

## Evidence chain

Each extraction run is hashed and linked to the previous run. If a provider
later claims the data never existed, the manifest shows what was exported,
when, and with which checksum. `moveon status` verifies the chain on every
call. `moveon escalate` includes it in the complaint.

## DPA routing

Move On ships a database of 31 supervisory authorities (27 EU, 3 EEA, UK)
with complaint addresses. By default it picks the authority of the
provider's EU establishment (Art. 56 GDPR): Ireland for OpenAI, Anthropic,
Google, Meta, xAI and Perplexity; France for Mistral. Pass `--country` to
file with the authority of your own residence instead (Art. 77 GDPR).

Sources: EDPB member list and [datenanfragen.de](https://www.datenanfragen.de) (CC BY 4.0).

## Privacy and security

- **No network at runtime.** A socket-blocking test in CI fails the build if
  any command opens a connection. The one exception is `escalate --send`,
  which is explicit and confirmed interactively.
- **Local files only.** `MOVEON.d/` is created with mode 0700, files with
  0600, and contains its own `.gitignore` so it cannot be committed by
  accident. Move On warns if the bundle sits inside a git repository.
- **Nothing leaks in errors.** Tracebacks never print local variables, which
  would contain your chats.
- **Defensive parsing.** Archives are checked for path traversal, encryption,
  and decompression bombs before anything is read.

Vulnerability reports: see [SECURITY.md](SECURITY.md).

## Shell completion

```bash
moveon --install-completion    # bash, zsh, fish, PowerShell
```

## Not legal advice

The letters cite the articles that apply in the common case. Art. 17(3)
GDPR lets a provider refuse deletion on specific grounds, and your
authority may prefer its own complaint form. Read what Move On generates
before you send it.

## Contributing

Parsers, templates for further languages, and corrections to the DPA
database are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
