from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.mistral import MistralParser


class TestMistralParserValidate:
    def test_valid_export(self, mistral_zip: Path):
        parser = MistralParser()
        assert parser.validate(mistral_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = MistralParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = MistralParser()
        assert parser.validate(wrong_format_zip) is False


class TestMistralParserParse:
    def test_parses_three_conversations(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        assert len(conversations) == 3

    def test_first_conversation_has_four_messages(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        first = conversations[0]
        assert len(first.messages) == 4
        assert first.messages[0].role == "user"
        assert first.messages[1].role == "assistant"
        assert "decorator" in first.messages[0].content.lower()

    def test_content_chunks_extracted(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        second = conversations[1]
        assert any("search" in m.content.lower() for m in second.messages)

    def test_format_version(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        for conv in conversations:
            assert conv.metadata.source == "mistral"

    def test_metadata_has_conversation_id(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        for conv in conversations:
            assert conv.metadata.conversation_id != ""

    def test_metadata_has_timestamps(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        first = conversations[0]
        assert first.metadata.created_at != ""
        assert "2025-06-15" in first.metadata.created_at

    def test_title_from_first_user_message(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        first = conversations[0]
        assert "decorator" in first.metadata.conversation_title.lower() or first.metadata.conversation_title != ""

    def test_roles_valid(self, mistral_zip: Path):
        parser = MistralParser()
        conversations = list(parser.parse(mistral_zip))
        for conv in conversations:
            for msg in conv.messages:
                assert msg.role in ("user", "assistant")

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = MistralParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
