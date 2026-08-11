from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from moveon.models import Conversation


class BaseParser(ABC):
    @abstractmethod
    def validate(self, path: Path) -> bool:
        """Return True if the archive at `path` is a valid export for this provider."""

    @abstractmethod
    def parse(self, path: Path) -> Iterator[Conversation]:
        """Yield normalized Conversation objects from the export archive."""
