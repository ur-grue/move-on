from __future__ import annotations

import json
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

from moveon.exceptions import ParseError
from moveon.models import Conversation, Message, Metadata
from moveon.parsers.base import BaseParser

CONTENT_TYPE_MAP = {
    "image": "image",
    "tool_use": "tool_use",
    "tool_result": "tool_use",
    "thinking": "thinking",
}


def _extract_content(content_blocks: list | str) -> str:
    if isinstance(content_blocks, str):
        return content_blocks

    parts = []
    for block in content_blocks:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            block_type = block.get("type", "text")
            if block_type == "text":
                parts.append(block.get("text", ""))
            else:
                mapped = CONTENT_TYPE_MAP.get(block_type, "unknown")
                parts.append(f"[non-text content: {mapped}]")
    return "\n".join(parts) if parts else ""


def _parse_conversation(conv: dict) -> Conversation | None:
    chat_messages = conv.get("chat_messages", [])
    if not chat_messages:
        return None

    messages = []
    for msg in chat_messages:
        role = msg.get("sender", "unknown")
        if role == "human":
            role = "user"
        elif role == "assistant":
            role = "assistant"

        content_blocks = msg.get("text", msg.get("content", ""))
        content = _extract_content(content_blocks)
        if not content:
            continue

        messages.append(Message(role=role, content=content))

    if not messages:
        return None

    metadata = Metadata(
        source="anthropic",
        conversation_id=conv.get("uuid", conv.get("id", "")),
        conversation_title=conv.get("name", ""),
        created_at=conv.get("created_at", ""),
        updated_at=conv.get("updated_at", ""),
    )

    return Conversation(messages=messages, metadata=metadata)


class AnthropicParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                return any(
                    n.endswith("conversations.json") or n.endswith("chats.json")
                    for n in names
                )
        except (zipfile.BadZipFile, OSError):
            return False

    def parse(self, path: Path) -> Iterator[Conversation]:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                conv_file = None
                for name in names:
                    if name.endswith("conversations.json") or name.endswith("chats.json"):
                        conv_file = name
                        break

                if conv_file is None:
                    raise ParseError(f"No conversations file found in {path}")

                with zf.open(conv_file) as f:
                    data = json.load(f)
        except zipfile.BadZipFile as e:
            raise ParseError(f"Not a valid ZIP file: {path}") from e
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in conversations file: {e}") from e

        if not isinstance(data, list):
            raise ParseError(
                f"Expected a list in conversations file, got {type(data).__name__}"
            )

        skipped = 0
        for conv in data:
            try:
                result = _parse_conversation(conv)
                if result is not None:
                    yield result
            except Exception as e:
                skipped += 1
                print(
                    f"Warning: Skipping conversation: {e}",
                    file=sys.stderr,
                )

        if skipped > 0:
            print(
                f"Warning: {skipped} conversation(s) skipped due to errors.",
                file=sys.stderr,
            )
