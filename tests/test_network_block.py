"""Socket-blocking test (FR-7).

Verifies that moveon runtime code does not open network sockets.
Scope: Python-level socket monkey-patch. Does not detect network access
via subprocesses or C extensions.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from moveon.cli import app

runner = CliRunner()


class BlockedSocket:
    def __init__(self, *args, **kwargs):
        raise OSError("Network access blocked by test")


class TestNetworkBlock:
    def test_extract_no_network(self, openai_zip: Path, tmp_path: Path):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["extract", "openai", str(openai_zip), "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_extract_google_no_network(self, google_zip: Path, tmp_path: Path):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["extract", "google", str(google_zip), "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_extract_meta_no_network(self, meta_zip: Path, tmp_path: Path):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["extract", "meta", str(meta_zip), "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_extract_xai_no_network(self, xai_zip: Path, tmp_path: Path):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["extract", "xai", str(xai_zip), "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_extract_mistral_no_network(self, mistral_zip: Path, tmp_path: Path):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["extract", "mistral", str(mistral_zip), "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_extract_perplexity_no_network(self, perplexity_zip: Path, tmp_path: Path):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["extract", "perplexity", str(perplexity_zip), "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_erase_no_network(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(
            app,
            ["extract", "openai", str(openai_zip), "--out", str(tmp_path)],
        )
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["erase", "openai", "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_status_no_network(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(
            app,
            ["extract", "openai", str(openai_zip), "--out", str(tmp_path)],
        )
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["status", "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_guide_no_network(self):
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(app, ["guide", "openai"])
            assert result.exit_code == 0

    def test_track_no_network(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(
            app,
            ["extract", "openai", str(openai_zip), "--out", str(tmp_path)],
        )
        with patch("socket.socket", BlockedSocket):
            result = runner.invoke(
                app,
                ["track", "openai", "--sent", "2026-08-01", "--out", str(tmp_path)],
            )
            assert result.exit_code == 0

    def test_escalate_mailto_no_network(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(
            app,
            ["extract", "openai", str(openai_zip), "--out", str(tmp_path)],
        )
        runner.invoke(
            app,
            ["track", "openai", "--sent", "2026-07-01", "--out", str(tmp_path)],
        )
        with (
            patch("socket.socket", BlockedSocket),
            patch("moveon.escalate.open_mailto", return_value=False),
        ):
            result = runner.invoke(
                app,
                ["escalate", "openai", "--out", str(tmp_path)],
            )
            assert result.exit_code == 0
