from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from moveon.parsers.base import BaseParser

from moveon.parsers.anthropic import AnthropicParser
from moveon.parsers.google import GoogleParser
from moveon.parsers.meta import MetaParser
from moveon.parsers.mistral import MistralParser
from moveon.parsers.openai import OpenAIParser
from moveon.parsers.perplexity import PerplexityParser
from moveon.parsers.xai import XaiParser

REGISTRY: dict[str, type[BaseParser]] = {
    "openai": OpenAIParser,
    "anthropic": AnthropicParser,
    "google": GoogleParser,
    "meta": MetaParser,
    "xai": XaiParser,
    "mistral": MistralParser,
    "perplexity": PerplexityParser,
}


def get_parser(provider: str) -> type[BaseParser]:
    parser_cls = REGISTRY.get(provider)
    if parser_cls is None:
        available = ", ".join(sorted(REGISTRY.keys()))
        msg = f"Unknown provider '{provider}'. Available: {available}"
        raise ValueError(msg)
    return parser_cls
