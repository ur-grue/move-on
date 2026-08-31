from __future__ import annotations

import json
import sys
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from moveon.exceptions import ParseError
from moveon.models import Conversation, Message, Metadata
from moveon.parsers.base import BaseParser

META_AI_SENDER_NAMES = frozenset({
    "Meta AI",
    "Meta-KI",
    "IA de Meta",
    "IA Meta",
})

MESSAGE_PATTERNS = [
    "message_1.json",
    "message.json",
]


def _is_meta_ai_thread(data: dict) -> bool:
    title = data.get("title", "")
    if "meta ai" in title.lower():
        return True

    participants = data.get("participants", [])
    return any(
        p.get("name", "") in META_AI_SENDER_NAMES
        for p in participants
    )


def _timestamp_ms_to_iso(ts_ms: int | float | None) -> str:
    if ts_ms is None:
        return ""
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=UTC).isoformat(timespec="seconds")
    except (ValueError, OSError, OverflowError):
        return ""


def _parse_thread(data: dict) -> Conversation | None:
    raw_messages = data.get("messages", [])
    if not raw_messages:
        return None

    sorted_msgs = sorted(raw_messages, key=lambda m: m.get("timestamp_ms", 0))

    messages = []
    for msg in sorted_msgs:
        content = msg.get("content", "")
        if not content:
            continue

        sender = msg.get("sender_name", "")
        role = "assistant" if sender in META_AI_SENDER_NAMES else "user"

        messages.append(Message(role=role, content=content))

    if not messages:
        return None

    thread_path = data.get("thread_path", "")
    conv_id = thread_path if thread_path else data.get("title", "meta-ai")

    timestamps = [m.get("timestamp_ms", 0) for m in sorted_msgs if m.get("timestamp_ms")]
    created_at = _timestamp_ms_to_iso(min(timestamps)) if timestamps else ""
    updated_at = _timestamp_ms_to_iso(max(timestamps)) if timestamps else ""

    metadata = Metadata(
        source="meta",
        conversation_id=conv_id,
        conversation_title=data.get("title", ""),
        created_at=created_at,
        updated_at=updated_at,
    )

    return Conversation(messages=messages, metadata=metadata)


class MetaParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                for name in names:
                    if not name.endswith(".json"):
                        continue
                    if "message" not in name.lower():
                        continue
                    try:
                        with zf.open(name) as f:
                            data = json.load(f)
                        if isinstance(data, dict) and _is_meta_ai_thread(data):
                            return True
                    except (json.JSONDecodeError, KeyError):
                        continue
                return False
        except (zipfile.BadZipFile, OSError):
            return False

    def parse(self, path: Path) -> Iterator[Conversation]:
        try:
            zf = zipfile.ZipFile(path)
        except zipfile.BadZipFile as e:
            raise ParseError(f"Not a valid ZIP file: {path}") from e

        skipped = 0
        found = 0
        with zf:
            for name in zf.namelist():
                if not name.endswith(".json"):
                    continue
                if not any(p in name.lower() for p in ("message", "meta_ai", "meta-ai")):
                    continue

                try:
                    with zf.open(name) as f:
                        data = json.load(f)
                except (json.JSONDecodeError, KeyError) as e:
                    skipped += 1
                    print(f"Warning: Skipping {name}: {e}", file=sys.stderr)
                    continue

                if not isinstance(data, dict):
                    continue

                if not _is_meta_ai_thread(data):
                    continue

                try:
                    conv = _parse_thread(data)
                    if conv is not None:
                        found += 1
                        yield conv
                except Exception as e:
                    skipped += 1
                    print(f"Warning: Skipping conversation in {name}: {e}", file=sys.stderr)

        if found == 0 and skipped == 0:
            print(
                "Warning: No Meta AI conversations found in archive.",
                file=sys.stderr,
            )

        if skipped > 0:
            print(
                f"Warning: {skipped} file(s) skipped due to errors.",
                file=sys.stderr,
            )
