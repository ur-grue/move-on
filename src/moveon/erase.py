from __future__ import annotations

import os
from importlib import resources
from pathlib import Path
from string import Template

from moveon.bundle import ensure_erase_dir, _write_secure


def _load_template(name: str) -> Template:
    template_dir = Path(__file__).parent / "templates"
    template_path = template_dir / name
    return Template(template_path.read_text(encoding="utf-8"))


def generate_erasure(
    bp: Path,
    provider: str,
    lang: str = "de",
) -> Path:
    template_name = f"{provider}-erasure-{lang}.txt"
    template = _load_template(template_name)
    content = template.safe_substitute(ACCOUNT_EMAIL="$ACCOUNT_EMAIL", DATE="$DATE")

    erase_dir = ensure_erase_dir(bp)
    output_file = erase_dir / f"{provider}-erasure-{lang}.md"
    _write_secure(output_file, content)
    return output_file


def generate_tracking(bp: Path, providers: list[str]) -> Path:
    template = _load_template("tracking.txt")

    rows = []
    for provider in sorted(providers):
        rows.append(f"| {provider} | ___ | ___ | ☐ | ☐ |")

    content = template.safe_substitute(PROVIDER_ROWS="\n".join(rows))

    erase_dir = ensure_erase_dir(bp)
    output_file = erase_dir / "TRACKING.md"
    _write_secure(output_file, content)
    return output_file


def generate_all_erasures(bp: Path, providers: list[str]) -> list[Path]:
    files = []
    for provider in providers:
        for lang in ("de", "en"):
            files.append(generate_erasure(bp, provider, lang))
    files.append(generate_tracking(bp, providers))
    return files
