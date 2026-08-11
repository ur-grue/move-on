from __future__ import annotations

from pathlib import Path

from moveon.bundle import ensure_bundle
from moveon.erase import generate_all_erasures, generate_erasure, generate_tracking


class TestEraseGeneration:
    def test_generate_german_template(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        f = generate_erasure(bp, "openai", "de")
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "Art. 17" in content
        assert "$ACCOUNT_EMAIL" in content
        assert "$DATE" in content
        assert "Kein Rechtsrat" in content

    def test_generate_english_template(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        f = generate_erasure(bp, "openai", "en")
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "Article 17" in content
        assert "$ACCOUNT_EMAIL" in content
        assert "Not legal advice" in content

    def test_anthropic_template(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        f = generate_erasure(bp, "anthropic", "de")
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "privacy@anthropic.com" in content

    def test_openai_submission_channel(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        f = generate_erasure(bp, "openai", "de")
        content = f.read_text(encoding="utf-8")
        assert "privacy.openai.com" in content

    def test_file_permissions_0600(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        f = generate_erasure(bp, "openai", "de")
        stat = f.stat()
        assert oct(stat.st_mode & 0o777) == "0o600"


class TestTracking:
    def test_generate_tracking(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        f = generate_tracking(bp, ["openai", "anthropic"])
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "openai" in content
        assert "anthropic" in content
        assert "Art. 12 Abs. 3" in content


class TestGenerateAll:
    def test_generates_all_files(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        files = generate_all_erasures(bp, ["openai", "anthropic"])
        assert len(files) == 5  # 2 providers * 2 langs + 1 tracking
        names = {f.name for f in files}
        assert "openai-erasure-de.md" in names
        assert "openai-erasure-en.md" in names
        assert "anthropic-erasure-de.md" in names
        assert "anthropic-erasure-en.md" in names
        assert "TRACKING.md" in names
