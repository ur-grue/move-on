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

BACKEND_PATTERNS = [
    "prod-grok-backend.json",
]


def _bson_timestamp_to_iso(ts_obj: dict | str | None) -> str:
    if ts_obj is None:
        return ""
    if isinstance(ts_obj, str):
        return ts_obj
    try:
        ms = int(ts_obj["$date"]["$numberLong"])
        return datetime.fromtimestamp(ms / 1000, tz=UTC).isoformat(timespec="seconds")
    except (KeyError, TypeError, ValueError, OSError, OverflowError):
        return ""


def _normalize_role(sender: str) -> str:
    if sender.lower() == "human":
        return "user"
    return "assistant"


def _parse_conversation(conv_wrapper: dict) -> Conversation | None:
    conv = conv_wrapper.get("conversation", {})
    responses = conv_wrapper.get("responses", [])

    if not responses:
        return None

    messages = []
    for resp_wrapper in responses:
        resp = resp_wrapper.get("response", resp_wrapper)
        content = resp.get("message", "")
        if not content:
            continue
        sender = resp.get("sender", "assistant")
        messages.append(Message(role=_normalize_role(sender), content=content))

    if not messages:
        return None

    conv_id = conv.get("id", "")
    title = conv.get("title", "")
    created_at = conv.get("create_time", "")
    updated_at = conv.get("modify_time", created_at)

    metadata = Metadata(
        source="xai",
        conversation_id=conv_id,
        conversation_title=title,
        created_at=created_at,
        updated_at=updated_at,
    )

    return Conversation(messages=messages, metadata=metadata)


class XaiParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                return any(
                    name.endswith("prod-grok-backend.json")
                    for name in names
                )
        except (zipfile.BadZipFile, OSError):
            return False

    def parse(self, path: Path) -> Iterator[Conversation]:
        try:
            with zipfile.ZipFile(path) as zf:
                matched = None
                for name in zf.namelist():
                    if name.endswith("prod-grok-backend.json"):
                        matched = name
                        break

                if matched is None:
                    raise ParseError(f"No prod-grok-backend.json found in {path}")

                with zf.open(matched) as f:
                    data = json.load(f)
        except zipfile.BadZipFile as e:
            raise ParseError(f"Not a valid ZIP file: {path}") from e
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in {matched}: {e}") from e

        conversations = data.get("conversations", data if isinstance(data, list) else [])

        if not isinstance(conversations, list):
            raise ParseError(
                f"Expected conversations list, got {type(conversations).__name__}"
            )

        skipped = 0
        for conv_wrapper in conversations:
            try:
                result = _parse_conversation(conv_wrapper)
                if result is not None:
                    yield result
            except Exception as e:
                skipped += 1
                print(f"Warning: Skipping conversation: {e}", file=sys.stderr)

        if skipped > 0:
            print(
                f"Warning: {skipped} conversation(s) skipped due to errors.",
                file=sys.stderr,
            )
