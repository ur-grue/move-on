from __future__ import annotations

from pathlib import Path
from string import Template

from moveon.bundle import _write_secure, ensure_erase_dir


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


def generate_tracking_from_manifest(bp: Path, manifest: object) -> Path:
    """Regenerate TRACKING.md from manifest erasure state."""
    erase_dir = ensure_erase_dir(bp)

    rows = []
    for provider in sorted(manifest.providers.keys()):
        pm = manifest.providers[provider]
        sent = pm.erasure_sent_at or "___"
        deadline = pm.erasure_deadline or "___"
        status = pm.erasure_status.value if pm.erasure_status else "pending"
        status_mark = {"pending": "☐", "sent": "☐", "overdue": "⚠", "complaint_filed": "☑"}
        answered = "☐"
        escalated = status_mark.get(status, "☐")
        rows.append(f"| {provider} | {sent} | {deadline} | {answered} | {escalated} |")

    template = _load_template("tracking.txt")
    content = template.safe_substitute(PROVIDER_ROWS="\n".join(rows))

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
