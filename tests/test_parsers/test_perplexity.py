from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.perplexity import PerplexityParser


class TestPerplexityParserValidate:
    def test_valid_export(self, perplexity_zip: Path):
        parser = PerplexityParser()
        assert parser.validate(perplexity_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = PerplexityParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = PerplexityParser()
        assert parser.validate(wrong_format_zip) is False


class TestPerplexityParserParse:
    def test_parses_three_threads(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        assert len(conversations) == 3

    def test_first_thread_has_four_messages(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        first = conversations[0]
        assert len(first.messages) == 4
        assert first.messages[0].role == "user"
        assert first.messages[1].role == "assistant"
        assert "async" in first.messages[0].content.lower()

    def test_single_step_thread(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        second = conversations[1]
        assert len(second.messages) == 2

    def test_format_version(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        for conv in conversations:
            assert conv.metadata.source == "perplexity"

    def test_metadata_has_slug_as_id(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        assert conversations[0].metadata.conversation_id == "pplx-thread-001"

    def test_metadata_has_title(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        assert conversations[0].metadata.conversation_title == "Python Async"

    def test_metadata_has_timestamps(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        first = conversations[0]
        assert first.metadata.created_at == "2025-06-15T10:00:00Z"
        assert first.metadata.updated_at == "2025-06-15T10:30:00Z"

    def test_roles_valid(self, perplexity_zip: Path):
        parser = PerplexityParser()
        conversations = list(parser.parse(perplexity_zip))
        for conv in conversations:
            for msg in conv.messages:
                assert msg.role in ("user", "assistant")

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = PerplexityParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
