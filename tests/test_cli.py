from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from moveon.cli import app
from moveon.guide import GUIDES
from moveon.parsers import REGISTRY

runner = CliRunner()


class TestRegistrySync:
    def test_parser_and_guide_registries_match(self):
        assert set(REGISTRY.keys()) == set(GUIDES.keys())


class TestVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.3.0" in result.output


class TestHelp:
    def test_help_shows_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "extract" in result.output
        assert "guide" in result.output
        assert "erase" in result.output
        assert "status" in result.output


class TestGuide:
    def test_guide_lists_providers(self):
        result = runner.invoke(app, ["guide"])
        assert result.exit_code == 0
        assert "openai" in result.output
        assert "anthropic" in result.output
        assert "google" in result.output
        assert "meta" in result.output

    def test_guide_openai(self):
        result = runner.invoke(app, ["guide", "openai"])
        assert result.exit_code == 0
        assert "ChatGPT" in result.output

    def test_guide_unknown_provider(self):
        result = runner.invoke(app, ["guide", "unknown"])
        assert result.exit_code == 1


class TestExtract:
    def test_extract_openai(self, openai_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Extracted" in result.output
        assert "3 conversations" in result.output

        bp = tmp_bundle / "MOVEON.d"
        assert bp.exists()
        assert (bp / "raw" / "openai" / "messages.jsonl").exists()
        assert (bp / "manifest.json").exists()
        assert (bp / ".gitignore").exists()

    def test_extract_anthropic(self, anthropic_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "anthropic", str(anthropic_zip), "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Extracted" in result.output
        assert "3 conversations" in result.output

    def test_extract_google(self, google_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "google", str(google_zip), "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Extracted" in result.output
        assert "3 conversations" in result.output

        bp = tmp_bundle / "MOVEON.d"
        assert (bp / "raw" / "google" / "messages.jsonl").exists()

    def test_extract_meta(self, meta_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "meta", str(meta_zip), "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Extracted" in result.output
        assert "3 conversations" in result.output

        bp = tmp_bundle / "MOVEON.d"
        assert (bp / "raw" / "meta" / "messages.jsonl").exists()

    def test_extract_corrupt_zip(self, corrupt_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "openai", str(corrupt_zip), "--out", str(tmp_bundle)])
        assert result.exit_code == 1

    def test_extract_unknown_provider(self, openai_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "unknown", str(openai_zip), "--out", str(tmp_bundle)])
        assert result.exit_code == 1

    def test_double_extract_with_force(self, openai_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        result = runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle), "--force"])
        assert result.exit_code == 0

        bp = tmp_bundle / "MOVEON.d"
        manifest_data = json.loads((bp / "manifest.json").read_text())
        assert len(manifest_data["providers"]["openai"]["runs"]) == 2

    def test_extract_creates_gitignore_inside_bundle(self, openai_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        bp = tmp_bundle / "MOVEON.d"
        gitignore = bp / ".gitignore"
        assert gitignore.exists()
        assert gitignore.read_text().strip() == "*"

    def test_extraction_warning_shown(self, openai_zip: Path, tmp_bundle: Path):
        result = runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        assert "plaintext" in result.output or "plaintext" in (result.stderr or "")

    def test_jsonl_format(self, openai_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        bp = tmp_bundle / "MOVEON.d"
        jsonl_path = bp / "raw" / "openai" / "messages.jsonl"
        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
        for line in lines:
            data = json.loads(line)
            assert "format_version" in data
            assert "messages" in data
            assert "metadata" in data
            assert data["metadata"]["source"] == "openai"


class TestErase:
    def test_erase_single_provider(self, openai_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        result = runner.invoke(app, ["erase", "openai", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Generated" in result.output

    def test_erase_all(self, openai_zip: Path, anthropic_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        runner.invoke(app, ["extract", "anthropic", str(anthropic_zip), "--out", str(tmp_bundle)])
        result = runner.invoke(app, ["erase", "--all", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "5 files" in result.output

    def test_erase_without_extract_warns(self, tmp_bundle: Path):
        result = runner.invoke(app, ["erase", "openai", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Warning" in result.output or "verifizieren" in result.output


class TestStatus:
    def test_status_no_bundle(self, tmp_bundle: Path):
        result = runner.invoke(app, ["status", "--out", str(tmp_bundle)])
        assert result.exit_code == 1

    def test_status_after_extract(self, openai_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        result = runner.invoke(app, ["status", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "openai" in result.output
        assert "Conversations" in result.output

    def test_status_json(self, openai_zip: Path, tmp_bundle: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_bundle)])
        result = runner.invoke(app, ["status", "--json", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "providers" in data
        assert "openai" in data["providers"]
