from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from moveon.bundle import sha256_string


@dataclass
class ConversationSummary:
    conversation_id: str
    title: str
    message_count: int
    content_hash: str


@dataclass
class DiffResult:
    added: list[ConversationSummary] = field(default_factory=list)
    removed: list[ConversationSummary] = field(default_factory=list)
    changed: list[tuple[ConversationSummary, ConversationSummary]] = field(default_factory=list)
    unchanged: int = 0


def _load_conversations(jsonl_path: Path) -> dict[str, ConversationSummary]:
    result = {}
    for line in jsonl_path.read_text(encoding="utf-8").strip().split("\n"):
        if not line:
            continue
        data = json.loads(line)
        messages = data.get("messages", [])
        content_hash = sha256_string(json.dumps(messages, sort_keys=True, ensure_ascii=False))
        meta = data.get("metadata", {})
        conv_id = meta.get("conversation_id", "")
        summary = ConversationSummary(
            conversation_id=conv_id,
            title=meta.get("conversation_title", ""),
            message_count=len(messages),
            content_hash=content_hash,
        )
        result[conv_id] = summary
    return result


def compute_diff(old_path: Path, new_path: Path) -> DiffResult:
    old_convs = _load_conversations(old_path)
    new_convs = _load_conversations(new_path)

    old_ids = set(old_convs.keys())
    new_ids = set(new_convs.keys())

    result = DiffResult()

    for cid in sorted(new_ids - old_ids):
        result.added.append(new_convs[cid])

    for cid in sorted(old_ids - new_ids):
        result.removed.append(old_convs[cid])

    for cid in sorted(old_ids & new_ids):
        old_conv = old_convs[cid]
        new_conv = new_convs[cid]
        if old_conv.content_hash != new_conv.content_hash:
            result.changed.append((old_conv, new_conv))
        else:
            result.unchanged += 1

    return result
