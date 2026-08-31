from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from moveon.parsers.base import BaseParser

_PARSER_PATHS: dict[str, tuple[str, str]] = {
    "openai": ("moveon.parsers.openai", "OpenAIParser"),
    "anthropic": ("moveon.parsers.anthropic", "AnthropicParser"),
    "google": ("moveon.parsers.google", "GoogleParser"),
    "meta": ("moveon.parsers.meta", "MetaParser"),
    "xai": ("moveon.parsers.xai", "XaiParser"),
    "mistral": ("moveon.parsers.mistral", "MistralParser"),
    "perplexity": ("moveon.parsers.perplexity", "PerplexityParser"),
}

REGISTRY: set[str] = set(_PARSER_PATHS)

_cache: dict[str, type[BaseParser]] = {}


def get_parser(provider: str) -> type[BaseParser]:
    if provider in _cache:
        return _cache[provider]
    entry = _PARSER_PATHS.get(provider)
    if entry is None:
        available = ", ".join(sorted(_PARSER_PATHS))
        msg = f"Unknown provider '{provider}'. Available: {available}"
        raise ValueError(msg)
    mod = importlib.import_module(entry[0])
    cls = getattr(mod, entry[1])
    _cache[provider] = cls
    return cls
