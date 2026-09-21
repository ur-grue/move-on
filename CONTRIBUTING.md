# Contributing

Thanks for helping people get their data back.

## Add a provider parser

The most useful contribution is a parser for a provider we don't support yet.

1. Create `src/moveon/parsers/<provider>.py`.
2. Subclass `BaseParser` and implement `validate()` and `parse()`.
   `parse()` must yield stable `conversation_id`s across exports — `moveon diff`
   depends on it.
3. Register the module and class in `_PARSER_PATHS` in `src/moveon/parsers/__init__.py`.
4. Add a synthetic fixture in `tests/fixtures/` (see `tests/create_fixtures.py`).
5. Add tests in `tests/test_parsers/test_<provider>.py`.
6. Add erasure templates `src/moveon/templates/<provider>-erasure-{de,en}.txt`
   and an export guide in `GUIDES` in `src/moveon/guide.py`.

## Development

```bash
git clone https://github.com/ur-grue/move-on.git
cd move-on
pip install -e ".[dev]"

ruff check . && ruff format --check .
mypy src/
pytest
```

CI runs the same three commands on Python 3.11–3.13.

## Ground rules

- **No network access in runtime code.** `tests/test_network_block.py` blocks
  sockets and will fail your PR otherwise. The only exception is the explicit
  `escalate --send` SMTP path.
- **No real user data in fixtures.** Generate synthetic exports with
  `tests/create_fixtures.py`.
- **Every parser ships with tests.**
- Keep the dependency list at typer + pydantic. Prefer the standard library.

## Reporting bugs

Open an issue with the provider, the `moveon --version` output, and the error
message. Never attach your export ZIP or `MOVEON.d/` — they contain your chats.
