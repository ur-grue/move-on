from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from moveon.parsers.base import BaseParser

from moveon.parsers.anthropic import AnthropicParser
from moveon.parsers.google import GoogleParser
from moveon.parsers.meta import MetaParser
from moveon.parsers.openai import OpenAIParser

REGISTRY: dict[str, type[BaseParser]] = {
    "openai": OpenAIParser,
    "anthropic": AnthropicParser,
    "google": GoogleParser,
    "meta": MetaParser,
}


def get_parser(provider: str) -> type[BaseParser]:
    parser_cls = REGISTRY.get(provider)
    if parser_cls is None:
        available = ", ".join(sorted(REGISTRY.keys()))
        msg = f"Unknown provider '{provider}'. Available: {available}"
        raise ValueError(msg)
    return parser_cls
