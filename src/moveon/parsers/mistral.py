from __future__ import annotations

import json
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

from moveon.exceptions import ParseError
from moveon.models import Conversation, Message, Metadata
from moveon.parsers.base import BaseParser


def _extract_content(msg: dict) -> str:
    content = msg.get("content", "")
    if content:
        return content

    chunks = msg.get("contentChunks")
    if not chunks:
        return ""

    parts = []
    for chunk in chunks:
        if isinstance(chunk, str):
            parts.append(chunk)
        elif isinstance(chunk, dict):
            chunk_type = chunk.get("type", "text")
            if chunk_type == "text":
                parts.append(chunk.get("content") or chunk.get("text") or "")
            elif chunk_type in ("tool_call", "reference", "custom_element"):
                parts.append(f"[non-text content: {chunk_type}]")
            elif chunk_type in ("image_url", "file_reference"):
                parts.append("[non-text content: image]")
            else:
                parts.append(f"[non-text content: {chunk_type}]")
    return "\n".join(p for p in parts if p)


def _parse_chat_file(messages_data: list, chat_id: str) -> Conversation | None:
    if not messages_data:
        return None

    sorted_msgs = sorted(messages_data, key=lambda m: m.get("createdAt", ""))

    messages = []
    for msg in sorted_msgs:
        role = msg.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        content = _extract_content(msg)
        if not content:
            continue
        messages.append(Message(role=role, content=content))

    if not messages:
        return None

    first_msg = sorted_msgs[0]
    last_msg = sorted_msgs[-1]

    first_user_content = ""
    for msg in sorted_msgs:
        if msg.get("role") == "user":
            first_user_content = _extract_content(msg)
            break

    metadata = Metadata(
        source="mistral",
        conversation_id=first_msg.get("chatId", chat_id),
        conversation_title=first_user_content[:80] if first_user_content else "",
        created_at=first_msg.get("createdAt", ""),
        updated_at=last_msg.get("createdAt", ""),
    )

    return Conversation(messages=messages, metadata=metadata)


class MistralParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                return any(name.startswith("chat-") and name.endswith(".json") for name in names)
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
            for name in sorted(zf.namelist()):
                if not name.endswith(".json"):
                    continue
                base = name.rsplit("/", 1)[-1]
                if not base.startswith("chat-"):
                    continue

                chat_id = base.removesuffix(".json")

                try:
                    with zf.open(name) as f:
                        data = json.load(f)
                except (json.JSONDecodeError, KeyError) as e:
                    skipped += 1
                    print(f"Warning: Skipping {name}: {e}", file=sys.stderr)
                    continue

                if not isinstance(data, list):
                    skipped += 1
                    continue

                try:
                    conv = _parse_chat_file(data, chat_id)
                    if conv is not None:
                        found += 1
                        yield conv
                except Exception as e:
                    skipped += 1
                    print(f"Warning: Skipping {name}: {e}", file=sys.stderr)

        if found == 0 and skipped == 0:
            print(
                "Warning: No Mistral conversations found in archive.",
                file=sys.stderr,
            )

        if skipped > 0:
            print(
                f"Warning: {skipped} file(s) skipped due to errors.",
                file=sys.stderr,
            )
