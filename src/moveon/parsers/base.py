from __future__ import annotations

import json
import sys
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Callable

from moveon.exceptions import ParseError
from moveon.models import Conversation


class BaseParser(ABC):
    @abstractmethod
    def validate(self, path: Path) -> bool:
        """Return True if the archive at `path` is a valid export for this provider."""

    @abstractmethod
    def parse(self, path: Path) -> Iterator[Conversation]:
        """Yield normalized Conversation objects from the export archive."""

    def _load_json_from_zip(
        self, path: Path, filename_patterns: list[str],
    ) -> tuple[list, str]:
        """Load and parse a JSON list from a ZIP archive.

        Returns (parsed_data, matched_filename).
        """
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                matched = None
                for name in names:
                    for pattern in filename_patterns:
                        if name == pattern or name.endswith(pattern):
                            matched = name
                            break
                    if matched:
                        break

                if matched is None:
                    raise ParseError(
                        f"No matching file found in {path}. "
                        f"Looked for: {', '.join(filename_patterns)}"
                    )

                with zf.open(matched) as f:
                    data = json.load(f)
        except zipfile.BadZipFile as e:
            raise ParseError(f"Not a valid ZIP file: {path}") from e
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in {matched}: {e}") from e

        if not isinstance(data, list):
            raise ParseError(
                f"Expected a list in {matched}, got {type(data).__name__}"
            )

        return data, matched

    def _iter_conversations(
        self,
        data: list,
        parse_fn: Callable[[dict], Conversation | None],
    ) -> Iterator[Conversation]:
        skipped = 0
        for item in data:
            try:
                result = parse_fn(item)
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
