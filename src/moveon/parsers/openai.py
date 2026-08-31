from __future__ import annotations

import json
import sys
import zipfile
from collections.abc import Iterator
from datetime import UTC
from pathlib import Path

from moveon.exceptions import ParseError
from moveon.models import Conversation, Message, Metadata
from moveon.parsers.base import BaseParser

NON_TEXT_TYPES = {
    "dalle": "image",
    "image": "image",
    "audio": "audio",
    "code": "code_output",
    "file": "file",
    "tool_use": "tool_use",
    "tether_browsing": "tool_use",
    "tether_quote": "tool_use",
    "execution_output": "code_output",
}


def _extract_content(message: dict) -> str:
    content = message.get("content")
    if content is None:
        content_type = message.get("content_type", "unknown")
        return f"[non-text content: {NON_TEXT_TYPES.get(content_type, 'unknown')}]"

    content_type = message.get("content_type", "text")
    if content_type == "text":
        parts = content.get("parts", [])
        text_parts = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                ct = part.get("content_type", "unknown")
                mapped = NON_TEXT_TYPES.get(ct, "unknown")
                text_parts.append(f"[non-text content: {mapped}]")
        return "\n".join(text_parts) if text_parts else ""

    if content_type == "multimodal_text":
        parts = content.get("parts", [])
        text_parts = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                ct = part.get("content_type") or part.get("asset_pointer") or "unknown"
                if ct == "image_asset_pointer" or "image" in str(ct):
                    text_parts.append("[non-text content: image]")
                else:
                    text_parts.append(f"[non-text content: {NON_TEXT_TYPES.get(ct, 'unknown')}]")
        return "\n".join(text_parts) if text_parts else ""

    mapped = NON_TEXT_TYPES.get(content_type, "unknown")
    return f"[non-text content: {mapped}]"


def _walk_active_path(mapping: dict, current_node: str | None = None) -> list[str]:
    """Walk from current_node back to root via parent pointers, return node IDs in order."""
    current_id = current_node

    if current_id is None or current_id not in mapping:
        best_depth = -1
        for node_id, node in mapping.items():
            if not node.get("children"):
                depth = 0
                nid = node_id
                seen = set()
                while nid and nid not in seen:
                    seen.add(nid)
                    depth += 1
                    nid = mapping.get(nid, {}).get("parent")
                if depth > best_depth:
                    best_depth = depth
                    current_id = node_id

    if current_id is None:
        return []

    path = []
    visited = set()
    node_id = current_id
    while node_id and node_id not in visited:
        visited.add(node_id)
        path.append(node_id)
        node_id = mapping.get(node_id, {}).get("parent")

    path.reverse()
    return path


def _parse_conversation(conv: dict) -> tuple[Conversation | None, int]:
    """Parse a single conversation dict. Returns (Conversation, branch_count)."""
    mapping = conv.get("mapping", {})
    if not mapping:
        return None, 0

    active_path = _walk_active_path(mapping, conv.get("current_node"))
    active_set = set(active_path)

    branch_count = 0
    for node_id, node in mapping.items():
        if node_id not in active_set and node.get("message"):
            branch_count += 1

    messages = []
    for node_id in active_path:
        node = mapping.get(node_id, {})
        msg = node.get("message")
        if msg is None:
            continue
        role = msg.get("author", {}).get("role", "unknown")
        if role == "system":
            continue
        content_text = _extract_content(msg)
        if not content_text:
            continue
        messages.append(Message(role=role, content=content_text))

    if not messages:
        return None, branch_count

    metadata = Metadata(
        source="openai",
        conversation_id=conv.get("id", conv.get("conversation_id", "")),
        conversation_title=conv.get("title", ""),
        created_at=_timestamp_to_iso(conv.get("create_time")),
        updated_at=_timestamp_to_iso(conv.get("update_time")),
    )

    return Conversation(messages=messages, metadata=metadata), branch_count


def _timestamp_to_iso(ts: float | int | None) -> str:
    if ts is None:
        return ""
    from datetime import datetime

    try:
        return datetime.fromtimestamp(ts, tz=UTC).isoformat(timespec="seconds")
    except (ValueError, OSError, OverflowError):
        return ""


class OpenAIParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                return "conversations.json" in zf.namelist()
        except (zipfile.BadZipFile, OSError):
            return False

    def parse(self, path: Path) -> Iterator[Conversation]:
        try:
            with zipfile.ZipFile(path) as zf, zf.open("conversations.json") as f:
                data = json.load(f)
        except zipfile.BadZipFile as e:
            raise ParseError(f"Not a valid ZIP file: {path}") from e
        except KeyError as e:
            raise ParseError(f"conversations.json not found in {path}") from e
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in conversations.json: {e}") from e

        if not isinstance(data, list):
            raise ParseError(f"Expected a list in conversations.json, got {type(data).__name__}")

        total_branches = 0
        skipped = 0
        for conv in data:
            try:
                result, branches = _parse_conversation(conv)
                total_branches += branches
                if result is not None:
                    yield result
            except Exception as e:
                skipped += 1
                print(
                    f"Warning: Skipping conversation: {e}",
                    file=sys.stderr,
                )

        if total_branches > 0:
            print(
                f"Note: {total_branches} branch message(s) in non-active paths were skipped.",
                file=sys.stderr,
            )
        if skipped > 0:
            print(
                f"Warning: {skipped} conversation(s) skipped due to errors.",
                file=sys.stderr,
            )
