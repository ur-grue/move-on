from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from moveon.models import Manifest

from moveon import __version__

app = typer.Typer(
    name="moveon",
    help="Extract your AI provider data. Request deletion. Move on.",
    no_args_is_help=True,
    add_completion=True,
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
    from moveon.exceptions import ParseError

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
    provider: str = typer.Argument(
        help="Provider name (openai, anthropic, google, meta, xai, mistral, perplexity)",
    ),
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
    from moveon.bundle import (
        check_git_warnings,
        ensure_bundle,
        print_extraction_warning,
        read_manifest,
        sha256_file,
        sha256_string,
        write_jsonl,
        write_manifest,
    )
    from moveon.models import ManifestRun, now_iso
    from moveon.parsers import get_parser

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
    from moveon.guide import get_guide, list_providers

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
    from moveon.bundle import check_git_warnings, ensure_bundle, read_manifest
    from moveon.erase import generate_all_erasures, generate_erasure
    from moveon.guide import list_providers

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
                "Extract and verify your export before requesting deletion.",
                err=True,
            )
        f = generate_erasure(bp, provider, lang)
        typer.echo(f"Generated: {f}")
    else:
        typer.echo("Specify a provider or use --all.", err=True)
        raise typer.Exit(1)

    check_git_warnings(bp)


@app.command()
def track(
    provider: str = typer.Argument(help="Provider name"),
    sent: str = typer.Option(
        ...,
        "--sent",
        help="Date erasure request was sent (YYYY-MM-DD)",
    ),
    country: str = typer.Option(
        None,
        "--country",
        help="Your country code (ISO 3166-1 alpha-2) for DPA routing per Art. 77 GDPR",
    ),
    out: Path = typer.Option(Path("."), "--out", help="Parent directory for MOVEON.d/"),
) -> None:
    """Record when an erasure request was sent. Calculates the GDPR Art. 12(3) deadline."""
    from datetime import date

    from moveon.bundle import bundle_path, read_manifest, write_manifest
    from moveon.dpa import get_dpa_for_provider, list_countries
    from moveon.models import ErasureStatus, calculate_deadline

    bp = bundle_path(out)

    if not bp.exists():
        typer.echo("No MOVEON.d/ bundle found. Run 'moveon extract' first.", err=True)
        raise typer.Exit(1)

    try:
        sent_date = date.fromisoformat(sent)
    except ValueError:
        typer.echo(f"Invalid date format: {sent}. Use YYYY-MM-DD.", err=True)
        raise typer.Exit(1) from None

    if country and country.upper() not in list_countries():
        typer.echo(
            f"Unknown country code: {country}. "
            f"Use ISO 3166-1 alpha-2 (e.g. DE, FR, AT).",
            err=True,
        )
        raise typer.Exit(1)

    manifest = read_manifest(bp)

    pm = manifest.providers.get(provider)
    if pm is None:
        typer.echo(f"No extraction found for '{provider}'. Run 'moveon extract' first.", err=True)
        raise typer.Exit(1)

    deadline = calculate_deadline(sent_date)
    pm.erasure_status = ErasureStatus.SENT
    pm.erasure_sent_at = sent_date.isoformat()
    pm.erasure_deadline = deadline.isoformat()

    today = date.today()
    if today > deadline:
        pm.erasure_status = ErasureStatus.OVERDUE

    write_manifest(bp, manifest)

    typer.echo(f"Tracked erasure request for {provider}:")
    typer.echo(f"  Sent:     {sent_date.isoformat()}")
    typer.echo(f"  Deadline: {deadline.isoformat()} (Art. 12(3) GDPR)")

    if pm.erasure_status == ErasureStatus.OVERDUE:
        typer.echo("  Status:   OVERDUE — deadline has passed")

    dpa = get_dpa_for_provider(provider, country)
    if dpa:
        typer.echo(f"\n  Supervisory authority: {dpa['authority_name_en']}")
        if dpa.get("email"):
            typer.echo(f"  Complaint email:       {dpa['email']}")
        elif dpa.get("complaint_url"):
            typer.echo(f"  Complaint form:        {dpa['complaint_url']}")
        typer.echo(f"  Website:            {dpa['website']}")

    _regenerate_tracking(bp, manifest)


def _regenerate_tracking(bp: Path, manifest: Manifest) -> None:
    from moveon.erase import generate_tracking_from_manifest

    generate_tracking_from_manifest(bp, manifest)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    country: str = typer.Option(
        None,
        "--country",
        help="Your country code (ISO 3166-1 alpha-2) for DPA routing",
    ),
    out: Path = typer.Option(Path("."), "--out", help="Parent directory for MOVEON.d/"),
) -> None:
    """Show extraction status, erasure deadlines, and escalation guidance."""
    import json
    from datetime import date

    from moveon.bundle import bundle_path, read_manifest, sha256_string, write_manifest
    from moveon.models import ErasureStatus

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

    today = date.today()
    has_overdue = False

    typer.echo("Move On Status")
    typer.echo("=" * 40)

    for provider in manifest.provider_names():
        run = manifest.latest_run(provider)
        if run is None:
            continue
        pm = manifest.providers[provider]

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

        if len(pm.runs) > 1:
            broken = manifest.verify_chain(provider)
            if broken:
                typer.echo(
                    f"  Evidence Chain: ✗ broken at run(s) {broken}",
                    err=True,
                )
            else:
                typer.echo("  Evidence Chain: ✓ intact")

        if pm.erasure_sent_at:
            typer.echo(f"  Erasure sent: {pm.erasure_sent_at}")
            typer.echo(f"  Deadline:     {pm.erasure_deadline}")

            if pm.erasure_deadline:
                deadline_date = date.fromisoformat(pm.erasure_deadline)
                if pm.erasure_status == ErasureStatus.COMPLAINT_FILED:
                    typer.echo("  Status: complaint filed")
                elif today > deadline_date:
                    pm.erasure_status = ErasureStatus.OVERDUE
                    has_overdue = True
                    days_over = (today - deadline_date).days
                    typer.echo(
                        f"  Status: OVERDUE by {days_over} day(s) "
                        "→ run 'moveon escalate' to file a complaint",
                        err=True,
                    )
                else:
                    days_left = (deadline_date - today).days
                    typer.echo(f"  Status: deadline running ({days_left} day(s) left)")
        else:
            typer.echo("  Erasure: not sent yet → 'moveon erase' + 'moveon track'")

    if has_overdue:
        write_manifest(bp, manifest)
        typer.echo("\n" + "=" * 40)
        typer.echo("At least one provider is overdue.")
        typer.echo("Next step: 'moveon escalate <provider>' to file a DPA complaint.")

    _regenerate_tracking(bp, manifest)


@app.command()
def diff(
    provider: str = typer.Argument(help="Provider name"),
    out: Path = typer.Option(Path("."), "--out", help="Parent directory for MOVEON.d/"),
) -> None:
    """Compare the last two extraction runs for a provider."""
    from moveon.bundle import bundle_path, read_manifest
    from moveon.diff import compute_diff

    bp = bundle_path(out)

    if not bp.exists():
        typer.echo("No MOVEON.d/ bundle found. Run 'moveon extract' first.", err=True)
        raise typer.Exit(1)

    manifest = read_manifest(bp)

    pm = manifest.providers.get(provider)
    if pm is None:
        typer.echo(f"No extractions found for '{provider}'.", err=True)
        raise typer.Exit(1)

    if len(pm.runs) < 2:
        typer.echo(
            "Only one extraction run found. "
            "Request a new export from the provider and run 'moveon extract' again.",
            err=True,
        )
        raise typer.Exit(1)

    old_run = pm.runs[-2]
    new_run = pm.runs[-1]

    if old_run.tool_version != new_run.tool_version:
        typer.echo(
            f"Warning: runs come from different moveon versions "
            f"({old_run.tool_version}, {new_run.tool_version}). "
            f"Results may differ.",
            err=True,
        )

    provider_dir = bp / "raw" / provider
    old_index = len(pm.runs) - 2
    old_path = provider_dir / f"messages-run-{old_index}.jsonl"
    new_path = provider_dir / "messages.jsonl"

    if not old_path.exists():
        typer.echo(
            f"Archived run file not found: {old_path}. "
            "Cannot compute diff without both run files.",
            err=True,
        )
        raise typer.Exit(1)

    if not new_path.exists():
        typer.echo(f"Current run file not found: {new_path}.", err=True)
        raise typer.Exit(1)

    result = compute_diff(old_path, new_path)

    typer.echo(f"Diff for {provider}: Run {old_index} → {old_index + 1}")
    typer.echo("=" * 40)
    typer.echo(f"  Added:     {len(result.added)} conversations")
    typer.echo(f"  Removed:   {len(result.removed)} conversations")
    typer.echo(f"  Changed:   {len(result.changed)} conversations")
    typer.echo(f"  Unchanged: {result.unchanged} conversations")

    if result.added:
        typer.echo("\nNew conversations:")
        for conv in result.added:
            title = conv.title or conv.conversation_id[:16]
            typer.echo(f"  + {title} ({conv.message_count} messages)")

    if result.removed:
        typer.echo("\nRemoved conversations:")
        for conv in result.removed:
            title = conv.title or conv.conversation_id[:16]
            typer.echo(f"  - {title} ({conv.message_count} messages)")

    if result.changed:
        typer.echo("\nChanged conversations:")
        for old_conv, new_conv in result.changed:
            title = new_conv.title or new_conv.conversation_id[:16]
            delta = new_conv.message_count - old_conv.message_count
            sign = "+" if delta > 0 else ""
            typer.echo(
                f"  ~ {title} ({old_conv.message_count} → "
                f"{new_conv.message_count} messages, {sign}{delta})"
            )


@app.command()
def escalate(
    provider: str = typer.Argument(help="Provider name"),
    lang: str = typer.Option("de", "--lang", help="Language (de or en)"),
    country: str = typer.Option(
        None,
        "--country",
        help="Your country code (ISO 3166-1 alpha-2) for DPA routing per Art. 77 GDPR",
    ),
    send: bool = typer.Option(False, "--send", help="Send via SMTP instead of mailto"),
    smtp_host: str = typer.Option(None, "--smtp-host", help="SMTP server hostname"),
    smtp_port: int = typer.Option(587, "--smtp-port", help="SMTP server port"),
    smtp_user: str = typer.Option(None, "--smtp-user", help="SMTP username"),
    smtp_pass: str = typer.Option(None, "--smtp-pass", help="SMTP password"),
    from_addr: str = typer.Option(None, "--from", help="Sender email address"),
    out: Path = typer.Option(Path("."), "--out", help="Parent directory for MOVEON.d/"),
) -> None:
    """Generate and send a GDPR Art. 77 complaint to the responsible DPA."""
    from moveon.bundle import bundle_path, read_manifest, write_manifest
    from moveon.dpa import get_dpa_for_provider
    from moveon.escalate import build_complaint_text, open_mailto, send_smtp
    from moveon.models import ErasureStatus

    if lang not in ("de", "en"):
        typer.echo(f"Unsupported language: {lang}. Use 'de' or 'en'.", err=True)
        raise typer.Exit(1)

    bp = bundle_path(out)
    if not bp.exists():
        typer.echo("No MOVEON.d/ bundle found. Run 'moveon extract' first.", err=True)
        raise typer.Exit(1)

    manifest = read_manifest(bp)
    pm = manifest.providers.get(provider)
    if pm is None:
        typer.echo(f"No extraction found for '{provider}'.", err=True)
        raise typer.Exit(1)

    if not pm.erasure_sent_at:
        typer.echo(
            f"No erasure request recorded for '{provider}'. "
            "Run 'moveon track' first.",
            err=True,
        )
        raise typer.Exit(1)

    dpa = get_dpa_for_provider(provider, country)
    if dpa is None:
        typer.echo("No responsible data protection authority found.", err=True)
        raise typer.Exit(1)

    subject = (
        f"Beschwerde nach Art. 77 DSGVO — {provider}"
        if lang == "de"
        else f"Complaint under Art. 77 GDPR — {provider}"
    )

    body = build_complaint_text(provider, pm, manifest, bp, lang)

    if send:
        if not smtp_host:
            typer.echo("--smtp-host required with --send.", err=True)
            raise typer.Exit(1)
        if not from_addr:
            typer.echo("--from required with --send.", err=True)
            raise typer.Exit(1)

        dpa_email = dpa.get("email")
        if not dpa_email:
            typer.echo(
                f"No email contact for {dpa['authority_name_en']}. "
                f"File the complaint via web form: {dpa.get('complaint_url', dpa['website'])}",
                err=True,
            )
            raise typer.Exit(1)

        is_tty = sys.stdin.isatty()
        if is_tty:
            typer.echo(f"Sending complaint to: {dpa_email}")
            typer.echo(f"From: {from_addr}")
            typer.echo(f"Via: {smtp_host}:{smtp_port}")
            confirm = typer.confirm("Send the complaint now?")
            if not confirm:
                raise typer.Exit(0)

        try:
            send_smtp(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                from_addr=from_addr,
                dpa_email=dpa_email,
                subject=subject,
                body=body,
                username=smtp_user,
                password=smtp_pass,
            )
            typer.echo(f"Complaint sent to {dpa_email}.")
        except Exception as e:
            typer.echo(f"SMTP error: {e}", err=True)
            raise typer.Exit(1) from e

        pm.erasure_status = ErasureStatus.COMPLAINT_FILED
        write_manifest(bp, manifest)

    else:
        dpa_email = dpa.get("email")

        if dpa_email:
            opened = open_mailto(dpa_email, subject, body)
            if opened:
                typer.echo(f"Opened your mail client with the complaint to {dpa_email}.")
                typer.echo("Review it, send it, then confirm below.")

                is_tty = sys.stdin.isatty()
                if is_tty:
                    confirm = typer.confirm("Did you send the complaint?")
                    if confirm:
                        pm.erasure_status = ErasureStatus.COMPLAINT_FILED
                        write_manifest(bp, manifest)
                        typer.echo("Status set to 'complaint_filed'.")
            else:
                typer.echo("No mail client available. Complaint text:", err=True)
                typer.echo("")
                typer.echo(f"To: {dpa_email}")
                typer.echo(f"Subject: {subject}")
                typer.echo("")
                typer.echo(body)
        else:
            typer.echo(
                f"No email contact for {dpa['authority_name_en']}.",
                err=True,
            )
            complaint_url = dpa.get("complaint_url", dpa["website"])
            typer.echo(f"File the complaint via web form: {complaint_url}", err=True)
            typer.echo("")
            typer.echo("Complaint text:")
            typer.echo("")
            typer.echo(body)
