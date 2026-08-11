# Contributing

## Parser-Plugins

Der einfachste Weg, beizutragen: einen neuen Provider-Parser schreiben.

1. Erstelle `src/moveon/parsers/<provider>.py`
2. Implementiere `BaseParser` mit `validate()` und `parse()`
3. Registriere den Parser in `src/moveon/parsers/__init__.py` (`REGISTRY`)
4. Erstelle synthetische Test-Fixtures in `tests/fixtures/`
5. Schreibe Tests in `tests/test_parsers/test_<provider>.py`

## Entwicklung

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Richtlinien

- Kein Netzwerkzugriff im Laufzeitcode
- Keine echten Nutzerdaten in Fixtures
- Tests für jeden neuen Parser
