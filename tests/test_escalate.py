from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from moveon.bundle import ensure_bundle, read_manifest, write_manifest
from moveon.cli import app
from moveon.escalate import build_complaint_text
from moveon.models import (
    ErasureStatus,
    Manifest,
    ManifestRun,
)

runner = CliRunner()


def _setup_manifest(
    tmp_bundle: Path,
    provider: str = "openai",
    with_erasure: bool = True,
) -> None:
    bp = ensure_bundle(tmp_bundle)
    manifest = Manifest()
    run = ManifestRun(
        source_file="test.zip",
        sha256="abc123def456",
        extracted_at="2026-08-01T00:00:00+00:00",
        message_count=42,
        conversation_count=5,
        tool_version="1.0.0",
    )
    manifest.add_run(provider, run)
    if with_erasure:
        pm = manifest.providers[provider]
        pm.erasure_status = ErasureStatus.OVERDUE
        pm.erasure_sent_at = "2026-07-01"
        pm.erasure_deadline = "2026-08-01"
    write_manifest(bp, manifest)


class TestBuildComplaintText:
    def test_german_complaint(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        pm = manifest.providers["openai"]
        text = build_complaint_text("openai", pm, manifest, tmp_bundle / "MOVEON.d", "de")
        assert "Art. 77 DSGVO" in text
        assert "openai" in text
        assert "2026-07-01" in text
        assert "2026-08-01" in text
        assert "Art. 17" in text
        assert "Art. 12 Abs. 3" in text
        assert "abc123def456" in text
        assert "$NAME" in text
        assert "Kein Rechtsrat" in text

    def test_english_complaint(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        pm = manifest.providers["openai"]
        text = build_complaint_text("openai", pm, manifest, tmp_bundle / "MOVEON.d", "en")
        assert "Art. 77 GDPR" in text
        assert "Art. 17 GDPR" in text
        assert "Art. 12(3)" in text
        assert "abc123def456" in text
        assert "Not legal advice" in text

    def test_complaint_includes_evidence_chain(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        pm = manifest.providers["openai"]
        text = build_complaint_text("openai", pm, manifest, tmp_bundle / "MOVEON.d", "de")
        assert "Evidence Chain" in text
        assert "intakt" in text

    def test_complaint_includes_message_count(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        pm = manifest.providers["openai"]
        text = build_complaint_text("openai", pm, manifest, tmp_bundle / "MOVEON.d", "de")
        assert "42 Nachrichten" in text
        assert "5 Konversationen" in text


class TestEscalateCommand:
    def test_escalate_no_bundle(self, tmp_bundle: Path):
        result = runner.invoke(app, ["escalate", "openai", "--out", str(tmp_bundle)])
        assert result.exit_code == 1

    def test_escalate_no_extraction(self, tmp_bundle: Path):
        ensure_bundle(tmp_bundle)
        manifest = Manifest()
        write_manifest(tmp_bundle / "MOVEON.d", manifest)
        result = runner.invoke(app, ["escalate", "openai", "--out", str(tmp_bundle)])
        assert result.exit_code == 1
        assert "No extraction" in result.output

    def test_escalate_no_erasure_tracked(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle, with_erasure=False)
        result = runner.invoke(app, ["escalate", "openai", "--out", str(tmp_bundle)])
        assert result.exit_code == 1
        assert "Löschantrag" in result.output or "track" in result.output

    @patch("moveon.escalate.open_mailto", return_value=True)
    def test_escalate_opens_mailto(self, mock_mailto, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        result = runner.invoke(app, ["escalate", "openai", "--out", str(tmp_bundle)], input="n\n")
        assert result.exit_code == 0
        mock_mailto.assert_called_once()
        call_args = mock_mailto.call_args
        assert "dataprotection.ie" in call_args[0][0]
        assert "Art. 77" in call_args[0][1]

    @patch("moveon.escalate.open_mailto", return_value=False)
    def test_escalate_fallback_stdout(self, mock_mailto, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        result = runner.invoke(app, ["escalate", "openai", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Art. 77" in result.output

    def test_escalate_with_country(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        with patch("moveon.escalate.open_mailto", return_value=False):
            result = runner.invoke(
                app, ["escalate", "openai", "--country", "DE", "--out", str(tmp_bundle)]
            )
        assert result.exit_code == 0
        assert "bfdi" in result.output

    def test_escalate_english(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        with patch("moveon.escalate.open_mailto", return_value=False):
            result = runner.invoke(
                app, ["escalate", "openai", "--lang", "en", "--out", str(tmp_bundle)]
            )
        assert result.exit_code == 0
        assert "Art. 77 GDPR" in result.output

    def test_escalate_send_requires_smtp_host(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        result = runner.invoke(
            app,
            ["escalate", "openai", "--send", "--out", str(tmp_bundle)],
        )
        assert result.exit_code == 1
        assert "--smtp-host" in result.output

    def test_escalate_send_requires_from(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        result = runner.invoke(
            app,
            [
                "escalate",
                "openai",
                "--send",
                "--smtp-host",
                "smtp.test.com",
                "--out",
                str(tmp_bundle),
            ],
        )
        assert result.exit_code == 1
        assert "--from" in result.output

    @patch("moveon.escalate.open_mailto", return_value=True)
    def test_escalate_confirms_sets_status(self, mock_mailto, tmp_bundle: Path):
        _setup_manifest(tmp_bundle)
        with patch("moveon.cli.sys") as mock_sys:
            mock_sys.stdin.isatty.return_value = True
            mock_sys.stderr = sys.stderr
            result = runner.invoke(
                app, ["escalate", "openai", "--out", str(tmp_bundle)], input="y\n"
            )
        assert result.exit_code == 0
        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        pm = manifest.providers["openai"]
        assert pm.erasure_status == ErasureStatus.COMPLAINT_FILED

    def test_escalate_france_no_email(self, tmp_bundle: Path):
        _setup_manifest(tmp_bundle, provider="mistral")
        with patch("moveon.escalate.open_mailto", return_value=False):
            result = runner.invoke(
                app,
                ["escalate", "mistral", "--country", "FR", "--out", str(tmp_bundle)],
            )
        assert result.exit_code == 0
        assert "web form" in result.output or "cnil.fr" in result.output

    def test_help_shows_escalate(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "escalate" in result.output
