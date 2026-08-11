from __future__ import annotations

from pathlib import Path

from moveon.bundle import (
    ensure_bundle,
    read_manifest,
    sha256_file,
    write_jsonl,
    write_manifest,
)
from moveon.models import Manifest, ManifestRun


class TestBundleCreation:
    def test_ensure_bundle_creates_directory(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        assert bp.exists()
        assert bp.name == "MOVEON.d"

    def test_bundle_permissions_0700(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        stat = bp.stat()
        assert oct(stat.st_mode & 0o777) == "0o700"

    def test_inner_gitignore_created(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        gitignore = bp / ".gitignore"
        assert gitignore.exists()
        assert gitignore.read_text() == "*\n"

    def test_file_permissions_0600(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        gitignore = bp / ".gitignore"
        stat = gitignore.stat()
        assert oct(stat.st_mode & 0o777) == "0o600"


class TestManifest:
    def test_read_empty_manifest(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        manifest = read_manifest(bp)
        assert manifest.version == "1"
        assert manifest.providers == {}

    def test_write_and_read_manifest(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()
        run = ManifestRun(
            source_file="export.zip",
            sha256="abc123",
            extracted_at="2026-01-01T00:00:00+00:00",
            message_count=100,
            conversation_count=10,
            tool_version="0.1.0",
        )
        manifest.add_run("openai", run)
        write_manifest(bp, manifest)

        loaded = read_manifest(bp)
        assert "openai" in loaded.providers
        assert loaded.providers["openai"].runs[0].message_count == 100

    def test_multiple_runs_preserved(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()

        for i in range(3):
            run = ManifestRun(
                source_file=f"export-{i}.zip",
                sha256=f"hash{i}",
                extracted_at="2026-01-01T00:00:00+00:00",
                message_count=i * 10,
                conversation_count=i,
                tool_version="0.1.0",
            )
            manifest.add_run("openai", run)

        write_manifest(bp, manifest)
        loaded = read_manifest(bp)
        assert len(loaded.providers["openai"].runs) == 3
        assert loaded.providers["openai"].active_run == 2


class TestJsonlWrite:
    def test_write_jsonl_creates_file(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()
        lines = ['{"test": 1}', '{"test": 2}']
        path = write_jsonl(bp, "openai", lines, manifest)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert content.count("\n") == 2  # join + trailing newline

    def test_write_jsonl_archives_old(self, tmp_bundle: Path):
        bp = ensure_bundle(tmp_bundle)
        manifest = Manifest()
        run = ManifestRun(
            source_file="old.zip",
            sha256="oldhash",
            extracted_at="2026-01-01T00:00:00+00:00",
            message_count=5,
            conversation_count=1,
            tool_version="0.1.0",
        )
        manifest.add_run("openai", run)

        raw_dir = bp / "raw" / "openai"
        raw_dir.mkdir(parents=True, exist_ok=True)
        old_file = raw_dir / "messages.jsonl"
        old_file.write_text("old content\n")

        write_jsonl(bp, "openai", ['{"new": true}'], manifest)

        archived = raw_dir / "messages-run-0.jsonl"
        assert archived.exists()
        assert archived.read_text() == "old content\n"


class TestSha256:
    def test_sha256_consistent(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n")
        h1 = sha256_file(test_file)
        h2 = sha256_file(test_file)
        assert h1 == h2
        assert len(h1) == 64
