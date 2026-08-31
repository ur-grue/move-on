from __future__ import annotations

from moveon.models import Manifest, ManifestRun

FIXTURE_RUN = ManifestRun(
    source_file="export.zip",
    sha256="abc123def456",
    extracted_at="2025-06-15T10:00:00+00:00",
    message_count=42,
    conversation_count=3,
    tool_version="0.3.0",
    output_sha256="out_hash_789",
)

EXPECTED_HASH = FIXTURE_RUN.hash_fields()


class TestHashFields:
    def test_hash_is_deterministic(self):
        run = ManifestRun(
            source_file="export.zip",
            sha256="abc123def456",
            extracted_at="2025-06-15T10:00:00+00:00",
            message_count=42,
            conversation_count=3,
            tool_version="0.3.0",
            output_sha256="out_hash_789",
        )
        assert run.hash_fields() == EXPECTED_HASH

    def test_hash_changes_with_field(self):
        run = ManifestRun(
            source_file="different.zip",
            sha256="abc123def456",
            extracted_at="2025-06-15T10:00:00+00:00",
            message_count=42,
            conversation_count=3,
            tool_version="0.3.0",
            output_sha256="out_hash_789",
        )
        assert run.hash_fields() != EXPECTED_HASH

    def test_hash_ignores_previous_run_hash(self):
        run = ManifestRun(
            source_file="export.zip",
            sha256="abc123def456",
            extracted_at="2025-06-15T10:00:00+00:00",
            message_count=42,
            conversation_count=3,
            tool_version="0.3.0",
            output_sha256="out_hash_789",
            previous_run_hash="should_be_ignored",
        )
        assert run.hash_fields() == EXPECTED_HASH

    def test_hash_stability_across_versions(self):
        """Pin the hash to catch accidental changes to HASH_FIELDS or serialization."""
        assert EXPECTED_HASH == "0b1fafd3ace5b1b817723f67c8bede2b6df8d5743f750a72e052cd6f42430ea4"


class TestEvidenceChain:
    def test_first_run_has_no_previous_hash(self):
        manifest = Manifest()
        run = ManifestRun(
            source_file="export.zip",
            sha256="aaa",
            extracted_at="2025-06-15T10:00:00+00:00",
            message_count=10,
            conversation_count=1,
            tool_version="0.3.0",
        )
        manifest.add_run("openai", run)
        assert manifest.providers["openai"].runs[0].previous_run_hash == ""

    def test_second_run_links_to_first(self):
        manifest = Manifest()
        run1 = ManifestRun(
            source_file="export1.zip",
            sha256="aaa",
            extracted_at="2025-06-15T10:00:00+00:00",
            message_count=10,
            conversation_count=1,
            tool_version="0.3.0",
        )
        manifest.add_run("openai", run1)

        run2 = ManifestRun(
            source_file="export2.zip",
            sha256="bbb",
            extracted_at="2025-06-16T10:00:00+00:00",
            message_count=20,
            conversation_count=2,
            tool_version="0.3.0",
        )
        manifest.add_run("openai", run2)

        stored_run2 = manifest.providers["openai"].runs[1]
        assert stored_run2.previous_run_hash == run1.hash_fields()

    def test_verify_chain_intact(self):
        manifest = Manifest()
        for i in range(3):
            run = ManifestRun(
                source_file=f"export{i}.zip",
                sha256=f"hash{i}",
                extracted_at=f"2025-06-{15 + i}T10:00:00+00:00",
                message_count=10 * (i + 1),
                conversation_count=i + 1,
                tool_version="0.3.0",
            )
            manifest.add_run("openai", run)

        broken = manifest.verify_chain("openai")
        assert broken == []

    def test_verify_chain_detects_tampering(self):
        manifest = Manifest()
        for i in range(3):
            run = ManifestRun(
                source_file=f"export{i}.zip",
                sha256=f"hash{i}",
                extracted_at=f"2025-06-{15 + i}T10:00:00+00:00",
                message_count=10 * (i + 1),
                conversation_count=i + 1,
                tool_version="0.3.0",
            )
            manifest.add_run("openai", run)

        manifest.providers["openai"].runs[1].message_count = 999

        broken = manifest.verify_chain("openai")
        assert 2 in broken

    def test_verify_chain_single_run_ok(self):
        manifest = Manifest()
        run = ManifestRun(
            source_file="export.zip",
            sha256="aaa",
            extracted_at="2025-06-15T10:00:00+00:00",
            message_count=10,
            conversation_count=1,
            tool_version="0.3.0",
        )
        manifest.add_run("openai", run)
        assert manifest.verify_chain("openai") == []

    def test_verify_chain_unknown_provider(self):
        manifest = Manifest()
        assert manifest.verify_chain("nonexistent") == []
