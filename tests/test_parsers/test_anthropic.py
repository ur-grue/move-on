from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.anthropic import AnthropicParser


class TestAnthropicParserValidate:
    def test_valid_export(self, anthropic_zip: Path):
        parser = AnthropicParser()
        assert parser.validate(anthropic_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = AnthropicParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = AnthropicParser()
        assert parser.validate(wrong_format_zip) is False


class TestAnthropicParserParse:
    def test_parses_all_conversations(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        assert len(conversations) == 3

    def test_conversation_has_messages(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        first = conversations[0]
        assert len(first.messages) >= 2
        assert first.messages[0].role == "user"

    def test_format_version(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        for conv in conversations:
            assert conv.metadata.source == "anthropic"

    def test_metadata_has_id_and_title(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        first = conversations[0]
        assert first.metadata.conversation_id == "conv-a001"
        assert first.metadata.conversation_title == "Rust Basics"

    def test_human_role_mapped_to_user(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        for conv in conversations:
            roles = {m.role for m in conv.messages}
            assert "human" not in roles

    def test_non_text_content_placeholder(self, anthropic_zip: Path):
        parser = AnthropicParser()
        conversations = list(parser.parse(anthropic_zip))
        tool_conv = conversations[1]
        has_non_text = any("[non-text content:" in m.content for m in tool_conv.messages)
        assert has_non_text

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = AnthropicParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
