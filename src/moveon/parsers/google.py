from __future__ import annotations

import hashlib
import re
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

from moveon.exceptions import ParseError
from moveon.models import Conversation, Message, Metadata
from moveon.parsers.base import BaseParser

ACTIVITY_PATTERNS = [
    "Takeout/My Activity/Gemini Apps/MyActivity.json",
    "My Activity/Gemini Apps/MyActivity.json",
    "MyActivity.json",
]

HTML_TAG_RE = re.compile(r"<[^>]+>")
CONVERSATION_GAP_SECONDS = 3600


def _strip_html(html: str) -> str:
    text = HTML_TAG_RE.sub("", html)
    return text.strip()


def _parse_entry(entry: dict) -> tuple[str, str, str]:
    """Extract (user_prompt, model_response, timestamp) from an activity entry."""
    timestamp = entry.get("time", "")

    user_prompt = ""
    subtitles = entry.get("subtitles", [])
    if subtitles:
        user_prompt = subtitles[0].get("value", "")

    model_response = ""
    safe_html = entry.get("safeHtmlItem", [])
    if safe_html:
        raw_html = safe_html[0].get("html", "")
        model_response = _strip_html(raw_html)

    return user_prompt, model_response, timestamp


def _group_into_conversations(
    entries: list[dict],
) -> list[list[dict]]:
    """Group activity entries into conversations by time proximity."""
    if not entries:
        return []

    sorted_entries = sorted(entries, key=lambda e: e.get("time", ""))

    groups: list[list[dict]] = [[sorted_entries[0]]]
    for entry in sorted_entries[1:]:
        prev_time = groups[-1][-1].get("time", "")
        curr_time = entry.get("time", "")

        if _time_gap_exceeds(prev_time, curr_time, CONVERSATION_GAP_SECONDS):
            groups.append([entry])
        else:
            groups[-1].append(entry)

    return groups


def _time_gap_exceeds(t1: str, t2: str, max_seconds: int) -> bool:
    from datetime import datetime, timezone

    try:
        dt1 = datetime.fromisoformat(t1.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(t2.replace("Z", "+00:00"))
        return abs((dt2 - dt1).total_seconds()) > max_seconds
    except (ValueError, AttributeError):
        return True


def _conversation_id_from_entries(entries: list[dict]) -> str:
    first_time = entries[0].get("time", "")
    first_prompt = ""
    subtitles = entries[0].get("subtitles", [])
    if subtitles:
        first_prompt = subtitles[0].get("value", "")
    raw = f"google:{first_time}:{first_prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _entries_to_conversation(entries: list[dict]) -> Conversation | None:
    messages = []
    for entry in entries:
        user_prompt, model_response, _ts = _parse_entry(entry)
        if user_prompt:
            messages.append(Message(role="user", content=user_prompt))
        if model_response:
            messages.append(Message(role="assistant", content=model_response))

    if not messages:
        return None

    first_time = entries[0].get("time", "")
    last_time = entries[-1].get("time", "")

    metadata = Metadata(
        source="google",
        conversation_id=_conversation_id_from_entries(entries),
        conversation_title="",
        created_at=first_time,
        updated_at=last_time,
    )

    return Conversation(messages=messages, metadata=metadata)


class GoogleParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                return any(
                    name.endswith("MyActivity.json")
                    for name in names
                )
        except (zipfile.BadZipFile, OSError):
            return False

    def parse(self, path: Path) -> Iterator[Conversation]:
        data, _matched = self._load_json_from_zip(path, ACTIVITY_PATTERNS)

        gemini_entries = [
            entry for entry in data
            if entry.get("header", "") in ("Gemini Apps", "Gemini")
            or "Gemini" in str(entry.get("products", []))
        ]

        if not gemini_entries:
            print(
                f"Warning: No Gemini entries found in {_matched}. "
                f"Found {len(data)} entries with other headers.",
                file=sys.stderr,
            )
            return

        groups = _group_into_conversations(gemini_entries)

        skipped = 0
        for group in groups:
            try:
                conv = _entries_to_conversation(group)
                if conv is not None:
                    yield conv
            except Exception as e:
                skipped += 1
                print(f"Warning: Skipping conversation: {e}", file=sys.stderr)

        if skipped > 0:
            print(
                f"Warning: {skipped} conversation(s) skipped due to errors.",
                file=sys.stderr,
            )
