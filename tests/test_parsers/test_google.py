from __future__ import annotations

from pathlib import Path

import pytest

from moveon.exceptions import ParseError
from moveon.parsers.google import GoogleParser


class TestGoogleParserValidate:
    def test_valid_export(self, google_zip: Path):
        parser = GoogleParser()
        assert parser.validate(google_zip) is True

    def test_corrupt_zip(self, corrupt_zip: Path):
        parser = GoogleParser()
        assert parser.validate(corrupt_zip) is False

    def test_wrong_format(self, wrong_format_zip: Path):
        parser = GoogleParser()
        assert parser.validate(wrong_format_zip) is False


class TestGoogleParserParse:
    def test_groups_by_time_proximity(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        assert len(conversations) == 3

    def test_first_conversation_has_four_messages(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        first = conversations[0]
        assert len(first.messages) == 4
        assert first.messages[0].role == "user"
        assert first.messages[1].role == "assistant"
        assert "Python" in first.messages[0].content

    def test_html_stripped_from_responses(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        first = conversations[0]
        for msg in first.messages:
            assert "<p>" not in msg.content
            assert "<b>" not in msg.content

    def test_format_version(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        for conv in conversations:
            assert conv.format_version == "1"

    def test_metadata_source(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        for conv in conversations:
            assert conv.metadata.source == "google"

    def test_metadata_has_timestamps(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        first = conversations[0]
        assert first.metadata.created_at != ""
        assert "2025-06-15" in first.metadata.created_at

    def test_metadata_has_conversation_id(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        for conv in conversations:
            assert conv.metadata.conversation_id != ""
            assert len(conv.metadata.conversation_id) == 16

    def test_non_gemini_entries_filtered(self, google_zip: Path):
        parser = GoogleParser()
        conversations = list(parser.parse(google_zip))
        for conv in conversations:
            for msg in conv.messages:
                assert msg.content != "python tutorial"

    def test_corrupt_zip_raises(self, corrupt_zip: Path):
        parser = GoogleParser()
        with pytest.raises(ParseError):
            list(parser.parse(corrupt_zip))
