from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import typer

from moveon import __version__
from moveon.bundle import (
    bundle_path,
    check_git_warnings,
    ensure_bundle,
    print_extraction_warning,
    read_manifest,
    sha256_file,
    sha256_string,
    write_jsonl,
    write_manifest,
)
from moveon.erase import generate_all_erasures, generate_erasure
from moveon.exceptions import ParseError
from moveon.guide import get_guide, list_providers
from moveon.models import ManifestRun, now_iso
from moveon.parsers import get_parser

app = typer.Typer(
    name="moveon",
    help="Extract your AI provider data. Request deletion. Move on.",
    no_args_is_help=True,
    add_completion=False,
)

MAX_UNCOMPRESSED_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"moveon {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


def _check_zip_security(zip_path: Path) -> None:
    try:
        with zipfile.ZipFile(zip_path) as zf:
            total_size = 0
            for info in zf.infolist():
                if ".." in info.filename or info.filename.startswith("/"):
                    raise ParseError(
                        f"Suspicious path in ZIP: {info.filename}. "
                        "Possible path traversal attack."
                    )
                if info.flag_bits & 0x1:
                    raise ParseError(
                        f"Encrypted ZIP archive: {zip_path}. "
                        "Move On cannot process encrypted archives."
                    )
                total_size += info.file_size

            if total_size > MAX_UNCOMPRESSED_SIZE:
                raise ParseError(
                    f"ZIP uncompressed size ({total_size / 1e9:.1f} GB) exceeds "
                    f"limit ({MAX_UNCOMPRESSED_SIZE / 1e9:.0f} GB). Possible zip bomb."
                )
    except zipfile.BadZipFile as e:
        raise ParseError(f"Not a valid ZIP file: {zip_path}") from e


@app.command()
def extract(
    provider: str = typer.Argument(help="Provider name (openai, anthropic)"),
    export_zip: Path = typer.Argument(
        help="Path to the export ZIP file",
        exists=True,
        readable=True,
    ),
    out: Path = typer.Option(
        Path("."),
        "--out",
        help="Parent directory for MOVEON.d/",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite without confirmation"),
    verbose: bool = typer.Option(False, "--verbose", help="Show additional details"),
) -> None:
    """Extract and normalize an AI provider data export."""
    try:
        parser_cls = get_parser(provider)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    _check_zip_security(export_zip)

    parser = parser_cls()
    if not parser.validate(export_zip):
        typer.echo(
            f"Error: {export_zip} does not appear to be a valid {provider} export.",
            err=True,
        )
        raise typer.Exit(1)

    bp = ensure_bundle(out)
    manifest = read_manifest(bp)

    pm = manifest.providers.get(provider)
    if pm and pm.runs and not force:
        is_tty = sys.stdin.isatty()
        if not is_tty:
            typer.echo(
                "Use --force to overwrite existing extraction (non-interactive mode).",
                err=True,
            )
            raise typer.Exit(1)
        confirm = typer.confirm(
            f"Provider '{provider}' already extracted. Overwrite?",
        )
        if not confirm:
            raise typer.Exit(0)

    conversations = list(parser.parse(export_zip))
    lines = []
    total_messages = 0
    for conv in conversations:
        total_messages += len(conv.messages)
        lines.append(conv.model_dump_json())

    jsonl_path = write_jsonl(bp, provider, lines, manifest)

    source_hash = sha256_file(export_zip)
    output_hash = sha256_string("\n".join(lines) + "\n") if lines else None

    run = ManifestRun(
        source_file=export_zip.name,
        sha256=source_hash,
        extracted_at=now_iso(),
        message_count=total_messages,
        conversation_count=len(conversations),
        tool_version=__version__,
        output_sha256=output_hash,
    )
    manifest.add_run(provider, run)
    write_manifest(bp, manifest)

    typer.echo(
        f"Extracted {len(conversations)} conversations "
        f"({total_messages} messages) from {provider} export."
    )

    if verbose:
        typer.echo(f"  Source: {export_zip}")
        typer.echo(f"  SHA-256: {source_hash}")
        typer.echo(f"  Output: {jsonl_path}")

    check_git_warnings(bp)
    print_extraction_warning()


@app.command()
def guide(
    provider: str = typer.Argument(None, help="Provider name (optional)"),
) -> None:
    """Show export instructions for a provider."""
    if provider is None:
        typer.echo("Available providers:")
        for p in list_providers():
            typer.echo(f"  - {p}")
        typer.echo("\nUse: moveon guide <provider>")
        return

    text = get_guide(provider)
    if text is None:
        typer.echo(f"Unknown provider: {provider}", err=True)
        typer.echo(f"Available: {', '.join(list_providers())}", err=True)
        raise typer.Exit(1)

    typer.echo(text)


@app.command()
def erase(
    provider: str = typer.Argument(None, help="Provider name (optional with --all)"),
    all_providers: bool = typer.Option(False, "--all", help="Generate for all extracted providers"),
    lang: str = typer.Option("de", "--lang", help="Language (de or en)"),
    out: Path = typer.Option(Path("."), "--out", help="Parent directory for MOVEON.d/"),
) -> None:
    """Generate GDPR erasure request letters."""
    if lang not in ("de", "en"):
        typer.echo(f"Unsupported language: {lang}. Use 'de' or 'en'.", err=True)
        raise typer.Exit(1)

    bp = ensure_bundle(out)
    manifest = read_manifest(bp)

    if all_providers:
        providers = manifest.provider_names()
        if not providers:
            providers = list_providers()
            typer.echo(
                "Warning: No exports in manifest. Generating templates for all known providers.",
                err=True,
            )
        files = generate_all_erasures(bp, providers)
        typer.echo(f"Generated {len(files)} files:")
        for f in files:
            typer.echo(f"  {f}")
    elif provider is not None:
        if provider not in (manifest.provider_names()):
            typer.echo(
                f"Warning: No export for '{provider}' in manifest. "
                "Export verifizieren vor Löschung empfohlen.",
                err=True,
            )
        f = generate_erasure(bp, provider, lang)
        typer.echo(f"Generated: {f}")
    else:
        typer.echo("Specify a provider or use --all.", err=True)
        raise typer.Exit(1)

    check_git_warnings(bp)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    out: Path = typer.Option(Path("."), "--out", help="Parent directory for MOVEON.d/"),
) -> None:
    """Show extraction status and manifest contents."""
    bp = bundle_path(out)

    if not bp.exists():
        typer.echo("No MOVEON.d/ bundle found. Run 'moveon extract' first.", err=True)
        raise typer.Exit(1)

    manifest = read_manifest(bp)

    if json_output:
        typer.echo(json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return

    if not manifest.providers:
        typer.echo("Bundle exists but no providers extracted yet.")
        return

    typer.echo("Move On Status")
    typer.echo("=" * 40)

    for provider in manifest.provider_names():
        run = manifest.latest_run(provider)
        if run is None:
            continue
        typer.echo(f"\n  Provider: {provider}")
        typer.echo(f"  Source:   {run.source_file}")
        typer.echo(f"  SHA-256:  {run.sha256[:16]}...")
        typer.echo(f"  Date:     {run.extracted_at}")
        typer.echo(f"  Conversations: {run.conversation_count}")
        typer.echo(f"  Messages:      {run.message_count}")

        if run.output_sha256:
            jsonl_path = bp / "raw" / provider / "messages.jsonl"
            if jsonl_path.exists():
                current_hash = sha256_string(jsonl_path.read_text(encoding="utf-8"))
                if current_hash == run.output_sha256:
                    typer.echo("  Integrity: ✓ output unchanged")
                else:
                    typer.echo("  Integrity: ✗ output modified since extraction!", err=True)
