from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.openai import OpenAIParser


class TestOpenAIParserValidate:
    def test_valid_export(self, openai_zip: Path):
        parser = OpenAIParser()
        assert parser.validate(openai_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = OpenAIParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = OpenAIParser()
        assert parser.validate(wrong_format_zip) is False


class TestOpenAIParserParse:
    def test_parses_all_conversations(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        assert len(conversations) == 3

    def test_conversation_has_messages(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        first = conversations[0]
        assert len(first.messages) >= 2
        assert first.messages[0].role == "user"
        assert "Python" in first.messages[0].content

    def test_format_version(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        for conv in conversations:
            assert conv.metadata.source == "openai"

    def test_metadata_has_id_and_title(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        first = conversations[0]
        assert first.metadata.conversation_id == "conv-001"
        assert first.metadata.conversation_title == "Python Help"

    def test_timestamps_iso_format(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        first = conversations[0]
        assert first.metadata.created_at != ""
        assert "T" in first.metadata.created_at

    def test_branch_walking_skips_branches(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        first = conversations[0]
        contents = [m.content for m in first.messages]
        assert "Use open() with a context manager." in contents or "pathlib" in str(contents)
        assert len(first.messages) == 3

    def test_non_text_content_placeholder(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        image_conv = conversations[1]
        has_non_text = any("[non-text content:" in m.content for m in image_conv.messages)
        assert has_non_text

    def test_system_messages_filtered(self, openai_zip: Path):
        parser = OpenAIParser()
        conversations = list(parser.parse(openai_zip))
        for conv in conversations:
            roles = [m.role for m in conv.messages]
            assert "system" not in roles

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = OpenAIParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
