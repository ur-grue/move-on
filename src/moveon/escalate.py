from __future__ import annotations

import webbrowser
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote

from moveon.models import Manifest, ProviderManifest


def build_complaint_text(
    provider: str,
    pm: ProviderManifest,
    manifest: Manifest,
    bp: Path,
    lang: str = "de",
) -> str:
    if lang == "de":
        return _build_complaint_de(provider, pm, manifest, bp)
    return _build_complaint_en(provider, pm, manifest, bp)


def _build_complaint_de(
    provider: str,
    pm: ProviderManifest,
    manifest: Manifest,
    bp: Path,
) -> str:
    run = pm.runs[pm.active_run] if pm.runs else None
    lines = [
        "Beschwerde nach Art. 77 DSGVO",
        "",
        "Sehr geehrte Damen und Herren,",
        "",
        f"hiermit lege ich Beschwerde gegen {provider} ein.",
        "",
        f"Am {pm.erasure_sent_at} habe ich einen Löschantrag nach Art. 17 DSGVO gestellt.",
        f"Die Frist nach Art. 12 Abs. 3 DSGVO (ein Kalendermonat) lief am "
        f"{pm.erasure_deadline} ab.",
        f"Bis heute ({date.today().isoformat()}) habe ich keine vollständige Antwort erhalten.",
        "",
        "Beweismittel:",
    ]

    if run:
        lines.append(f"- Datenexport: {run.source_file} (SHA-256: {run.sha256})")
        lines.append(f"- Extrahiert am: {run.extracted_at}")
        lines.append(f"- {run.conversation_count} Konversationen, {run.message_count} Nachrichten")

    chain_status = "intakt"
    broken = manifest.verify_chain(provider)
    if broken:
        chain_status = f"gebrochen bei Run(s) {broken}"
    lines.append(f"- Evidence Chain: {chain_status}")

    erasure_path = bp / "erase" / f"{provider}-erasure-de.md"
    if erasure_path.exists():
        lines.append(f"- Kopie des Löschantrags liegt bei: {erasure_path.name}")

    lines.extend(
        [
            "",
            "Ich bitte um Prüfung und Durchsetzung meiner Rechte.",
            "",
            "Mit freundlichen Grüßen",
            "$NAME",
            "$ACCOUNT_EMAIL",
            "",
            "---",
            "Erstellt mit Move On (https://github.com/ur-grue/move-on)",
            "Kein Rechtsrat. Datenschutzrechtliche Beratung empfohlen.",
        ]
    )
    return "\n".join(lines)


def _build_complaint_en(
    provider: str,
    pm: ProviderManifest,
    manifest: Manifest,
    bp: Path,
) -> str:
    run = pm.runs[pm.active_run] if pm.runs else None
    lines = [
        "Complaint under Art. 77 GDPR",
        "",
        "Dear Sir or Madam,",
        "",
        f"I hereby file a complaint against {provider}.",
        "",
        f"On {pm.erasure_sent_at}, I submitted an erasure request under Art. 17 GDPR.",
        f"The deadline under Art. 12(3) GDPR (one calendar month) expired on "
        f"{pm.erasure_deadline}.",
        f"As of today ({date.today().isoformat()}), I have not received a complete response.",
        "",
        "Evidence:",
    ]

    if run:
        lines.append(f"- Data export: {run.source_file} (SHA-256: {run.sha256})")
        lines.append(f"- Extracted on: {run.extracted_at}")
        lines.append(f"- {run.conversation_count} conversations, {run.message_count} messages")

    chain_status = "intact"
    broken = manifest.verify_chain(provider)
    if broken:
        chain_status = f"broken at run(s) {broken}"
    lines.append(f"- Evidence chain: {chain_status}")

    erasure_path = bp / "erase" / f"{provider}-erasure-en.md"
    if erasure_path.exists():
        lines.append(f"- Copy of erasure request attached: {erasure_path.name}")

    lines.extend(
        [
            "",
            "I request that you investigate and enforce my rights.",
            "",
            "Yours faithfully,",
            "$NAME",
            "$ACCOUNT_EMAIL",
            "",
            "---",
            "Generated with Move On (https://github.com/ur-grue/move-on)",
            "Not legal advice. Data protection counsel recommended.",
        ]
    )
    return "\n".join(lines)


def open_mailto(dpa_email: str, subject: str, body: str) -> bool:
    mailto = f"mailto:{dpa_email}?subject={quote(subject)}&body={quote(body)}"
    try:
        webbrowser.open(mailto)
        return True
    except Exception:
        return False


def send_smtp(
    smtp_host: str,
    smtp_port: int,
    from_addr: str,
    dpa_email: str,
    subject: str,
    body: str,
    username: str | None = None,
    password: str | None = None,
    use_tls: bool = True,
) -> None:
    import smtplib

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = dpa_email
    msg["Subject"] = subject
    msg.set_content(body)

    if use_tls:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if username and password:
                server.login(username, password)
            server.send_message(msg)
