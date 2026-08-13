from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.meta import MetaParser


class TestMetaParserValidate:
    def test_valid_export(self, meta_zip: Path):
        parser = MetaParser()
        assert parser.validate(meta_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = MetaParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = MetaParser()
        assert parser.validate(wrong_format_zip) is False


class TestMetaParserParse:
    def test_parses_all_meta_ai_threads(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        assert len(conversations) == 3

    def test_first_conversation_has_messages(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        longest = max(conversations, key=lambda c: len(c.messages))
        assert len(longest.messages) == 4
        roles = [m.role for m in longest.messages]
        assert roles == ["user", "assistant", "user", "assistant"]

    def test_role_detection(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            for msg in conv.messages:
                assert msg.role in ("user", "assistant")

    def test_format_version(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            assert conv.metadata.source == "meta"

    def test_metadata_has_timestamps(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            assert conv.metadata.created_at != ""
            assert "T" in conv.metadata.created_at

    def test_metadata_has_conversation_id(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            assert conv.metadata.conversation_id != ""

    def test_metadata_has_title(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            assert conv.metadata.conversation_title == "Meta AI"

    def test_skips_non_meta_ai_threads(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        for conv in conversations:
            assert conv.metadata.conversation_title != "Friend"

    def test_messages_sorted_by_timestamp(self, meta_zip: Path):
        parser = MetaParser()
        conversations = list(parser.parse(meta_zip))
        longest = max(conversations, key=lambda c: len(c.messages))
        assert "weather" in longest.messages[0].content.lower()

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = MetaParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
