from __future__ import annotations

import json
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

from moveon.exceptions import ParseError
from moveon.models import Conversation, Message, Metadata
from moveon.parsers.base import BaseParser

THREADS_PATTERNS = [
    "threads.json",
    "search_threads.json",
]


def _parse_thread(thread: dict) -> Conversation | None:
    steps = thread.get("steps", [])
    if not steps:
        return None

    messages = []
    for step in steps:
        query = step.get("query_str", "")
        response = step.get("final_response", "")
        if query:
            messages.append(Message(role="user", content=query))
        if response:
            messages.append(Message(role="assistant", content=response))

    if not messages:
        return None

    slug = thread.get("slug", thread.get("id", ""))
    title = thread.get("title", "")

    metadata = Metadata(
        source="perplexity",
        conversation_id=slug,
        conversation_title=title,
        created_at=thread.get("created_at", thread.get("createdTime", "")),
        updated_at=thread.get("updated_at", thread.get("lastModifiedTime", "")),
    )

    return Conversation(messages=messages, metadata=metadata)


class PerplexityParser(BaseParser):
    def validate(self, path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                for name in names:
                    if any(name.endswith(p) for p in THREADS_PATTERNS):
                        return True
                    if name.endswith(".json"):
                        try:
                            with zf.open(name) as f:
                                data = json.load(f)
                            if isinstance(data, list) and data:
                                first = data[0]
                                if isinstance(first, dict) and "steps" in first:
                                    return True
                            elif isinstance(data, dict) and "threads" in data:
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

        threads = []
        with zf:
            for name in zf.namelist():
                if not name.endswith(".json"):
                    continue
                try:
                    with zf.open(name) as f:
                        data = json.load(f)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Skipping {name}: {e}", file=sys.stderr)
                    continue

                if isinstance(data, dict) and "threads" in data:
                    threads.extend(data["threads"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "steps" in item:
                            threads.append(item)

        if not threads:
            print(
                "Warning: No Perplexity threads found in archive.",
                file=sys.stderr,
            )
            return

        skipped = 0
        for thread in threads:
            try:
                conv = _parse_thread(thread)
                if conv is not None:
                    yield conv
            except Exception as e:
                skipped += 1
                print(f"Warning: Skipping thread: {e}", file=sys.stderr)

        if skipped > 0:
            print(
                f"Warning: {skipped} thread(s) skipped due to errors.",
                file=sys.stderr,
            )
