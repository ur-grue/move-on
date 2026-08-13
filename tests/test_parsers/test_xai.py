from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.xai import XaiParser


class TestXaiParserValidate:
    def test_valid_export(self, xai_zip: Path):
        parser = XaiParser()
        assert parser.validate(xai_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = XaiParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = XaiParser()
        assert parser.validate(wrong_format_zip) is False


class TestXaiParserParse:
    def test_parses_three_conversations(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        assert len(conversations) == 3

    def test_first_conversation_has_four_messages(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        first = conversations[0]
        assert len(first.messages) == 4
        assert first.messages[0].role == "user"
        assert first.messages[1].role == "assistant"
        assert "list comprehension" in first.messages[0].content

    def test_sender_normalization(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        for conv in conversations:
            for msg in conv.messages:
                assert msg.role in ("user", "assistant")

    def test_uppercase_assistant_normalized(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        second = conversations[1]
        assert second.messages[1].role == "assistant"

    def test_model_name_sender_normalized(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        third = conversations[2]
        assert third.messages[1].role == "assistant"

    def test_format_version(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        for conv in conversations:
            assert conv.metadata.source == "xai"

    def test_metadata_has_conversation_id(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        for conv in conversations:
            assert conv.metadata.conversation_id != ""

    def test_metadata_has_title(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        assert conversations[0].metadata.conversation_title == "Python Basics"

    def test_metadata_has_timestamps(self, xai_zip: Path):
        parser = XaiParser()
        conversations = list(parser.parse(xai_zip))
        first = conversations[0]
        assert first.metadata.created_at == "2025-06-15T10:00:00Z"

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = XaiParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
