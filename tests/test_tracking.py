from __future__ import annotations

from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from moveon.bundle import ensure_bundle, read_manifest, write_manifest
from moveon.cli import app
from moveon.models import (
    ErasureStatus,
    Manifest,
    ManifestRun,
    ProviderManifest,
    calculate_deadline,
)

runner = CliRunner()


class TestCalculateDeadline:
    def test_normal_month(self):
        assert calculate_deadline(date(2026, 1, 15)) == date(2026, 2, 15)

    def test_end_of_january(self):
        assert calculate_deadline(date(2026, 1, 31)) == date(2026, 2, 28)

    def test_leap_year(self):
        assert calculate_deadline(date(2028, 1, 31)) == date(2028, 2, 29)

    def test_december_to_january(self):
        assert calculate_deadline(date(2026, 12, 15)) == date(2027, 1, 15)

    def test_march_31_to_april_30(self):
        assert calculate_deadline(date(2026, 3, 31)) == date(2026, 4, 30)

    def test_first_of_month(self):
        assert calculate_deadline(date(2026, 8, 1)) == date(2026, 9, 1)

    def test_feb_28_to_march_28(self):
        assert calculate_deadline(date(2026, 2, 28)) == date(2026, 3, 28)


class TestErasureStatusEnum:
    def test_values(self):
        assert ErasureStatus.PENDING.value == "pending"
        assert ErasureStatus.SENT.value == "sent"
        assert ErasureStatus.OVERDUE.value == "overdue"
        assert ErasureStatus.COMPLAINT_FILED.value == "complaint_filed"


class TestProviderManifestErasureFields:
    def test_defaults(self):
        pm = ProviderManifest()
        assert pm.erasure_status == ErasureStatus.PENDING
        assert pm.erasure_sent_at is None
        assert pm.erasure_deadline is None

    def test_set_erasure_fields(self):
        pm = ProviderManifest(
            erasure_status=ErasureStatus.SENT,
            erasure_sent_at="2026-08-01",
            erasure_deadline="2026-09-01",
        )
        assert pm.erasure_status == ErasureStatus.SENT
        assert pm.erasure_sent_at == "2026-08-01"
        assert pm.erasure_deadline == "2026-09-01"

    def test_serialization_roundtrip(self):
        pm = ProviderManifest(
            erasure_status=ErasureStatus.OVERDUE,
            erasure_sent_at="2026-07-01",
            erasure_deadline="2026-08-01",
        )
        data = pm.model_dump(mode="json")
        restored = ProviderManifest.model_validate(data)
        assert restored.erasure_status == ErasureStatus.OVERDUE
        assert restored.erasure_sent_at == "2026-07-01"


class TestTrackCommand:
    def _setup_manifest(self, tmp_bundle: Path) -> None:
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()
        run = ManifestRun(
            source_file="test.zip",
            sha256="abc123",
            extracted_at="2026-08-01T00:00:00+00:00",
            message_count=10,
            conversation_count=2,
            tool_version="1.0.0",
        )
        manifest.add_run("openai", run)
        write_manifest(bp, manifest)

    def test_track_sets_sent_date(self, tmp_bundle: Path):
        # Use today so the deadline is always in the future, regardless of when tests run.
        sent = date.today()
        deadline = calculate_deadline(sent)
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app, ["track", "openai", "--sent", sent.isoformat(), "--out", str(tmp_bundle)]
        )
        assert result.exit_code == 0
        assert sent.isoformat() in result.output
        assert deadline.isoformat() in result.output

        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        pm = manifest.providers["openai"]
        assert pm.erasure_sent_at == sent.isoformat()
        assert pm.erasure_deadline == deadline.isoformat()
        assert pm.erasure_status == ErasureStatus.SENT

    def test_track_past_date_marks_overdue(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app, ["track", "openai", "--sent", "2020-01-01", "--out", str(tmp_bundle)]
        )
        assert result.exit_code == 0
        assert "OVERDUE" in result.output

        manifest = read_manifest(tmp_bundle / "MOVEON.d")
        assert manifest.providers["openai"].erasure_status == ErasureStatus.OVERDUE

    def test_track_invalid_date(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app, ["track", "openai", "--sent", "not-a-date", "--out", str(tmp_bundle)]
        )
        assert result.exit_code == 1
        assert "Invalid date" in result.output

    def test_track_unknown_provider(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app, ["track", "unknown", "--sent", "2026-08-01", "--out", str(tmp_bundle)]
        )
        assert result.exit_code == 1
        assert "No extraction" in result.output

    def test_track_no_bundle(self, tmp_bundle: Path):
        result = runner.invoke(
            app, ["track", "openai", "--sent", "2026-08-01", "--out", str(tmp_bundle)]
        )
        assert result.exit_code == 1

    def test_track_shows_dpa(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app, ["track", "openai", "--sent", "2026-08-01", "--out", str(tmp_bundle)]
        )
        assert result.exit_code == 0
        assert "Data Protection" in result.output or "Behörde" in result.output

    def test_track_with_country(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app,
            ["track", "openai", "--sent", "2026-08-01", "--country", "DE", "--out", str(tmp_bundle)],
        )
        assert result.exit_code == 0
        assert "Datenschutz" in result.output or "Data Protection" in result.output

    def test_track_invalid_country(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        result = runner.invoke(
            app,
            ["track", "openai", "--sent", "2026-08-01", "--country", "XX", "--out", str(tmp_bundle)],
        )
        assert result.exit_code == 1
        assert "Unknown country" in result.output

    def test_track_regenerates_tracking_md(self, tmp_bundle: Path):
        self._setup_manifest(tmp_bundle)
        runner.invoke(
            app, ["track", "openai", "--sent", "2026-08-01", "--out", str(tmp_bundle)]
        )
        tracking_path = tmp_bundle / "MOVEON.d" / "erase" / "TRACKING.md"
        assert tracking_path.exists()
        content = tracking_path.read_text(encoding="utf-8")
        assert "2026-08-01" in content
        assert "2026-09-01" in content


class TestStatusWithErasure:
    def _setup_with_erasure(self, tmp_bundle: Path, status: ErasureStatus = ErasureStatus.SENT) -> None:
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()
        run = ManifestRun(
            source_file="test.zip",
            sha256="abc123",
            extracted_at="2026-08-01T00:00:00+00:00",
            message_count=10,
            conversation_count=2,
            tool_version="1.0.0",
        )
        manifest.add_run("openai", run)
        pm = manifest.providers["openai"]
        pm.erasure_status = status
        pm.erasure_sent_at = "2026-08-01"
        pm.erasure_deadline = "2026-09-01"
        write_manifest(bp, manifest)

    def test_status_shows_erasure_info(self, tmp_bundle: Path):
        self._setup_with_erasure(tmp_bundle)
        result = runner.invoke(app, ["status", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "2026-08-01" in result.output
        assert "2026-09-01" in result.output

    def test_status_shows_no_erasure(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()
        run = ManifestRun(
            source_file="test.zip",
            sha256="abc123",
            extracted_at="2026-08-01T00:00:00+00:00",
            message_count=10,
            conversation_count=2,
            tool_version="1.0.0",
        )
        manifest.add_run("openai", run)
        write_manifest(bp, manifest)
        result = runner.invoke(app, ["status", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Noch nicht versendet" in result.output

    def test_status_json_includes_erasure(self, tmp_bundle: Path):
        self._setup_with_erasure(tmp_bundle)
        result = runner.invoke(app, ["status", "--json", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        pm = data["providers"]["openai"]
        assert pm["erasure_status"] == "sent"
        assert pm["erasure_sent_at"] == "2026-08-01"
        assert pm["erasure_deadline"] == "2026-09-01"

    def test_status_complaint_filed(self, tmp_bundle: Path):
        self._setup_with_erasure(tmp_bundle, ErasureStatus.COMPLAINT_FILED)
        result = runner.invoke(app, ["status", "--out", str(tmp_bundle)])
        assert result.exit_code == 0
        assert "Beschwerde eingereicht" in result.output

    def test_help_shows_track(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "track" in result.output
