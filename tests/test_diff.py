from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from moveon.cli import app
from moveon.diff import compute_diff

runner = CliRunner()


def _write_jsonl(path: Path, conversations: list[dict]) -> None:
    lines = [json.dumps(c) for c in conversations]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_conv(conv_id: str, title: str, messages: list[dict]) -> dict:
    return {
        "format_version": "1",
        "messages": messages,
        "metadata": {
            "source": "test",
            "conversation_id": conv_id,
            "conversation_title": title,
        },
    }


CONV_A = _make_conv("conv-a", "Topic A", [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there"},
])

CONV_B = _make_conv("conv-b", "Topic B", [
    {"role": "user", "content": "Question"},
    {"role": "assistant", "content": "Answer"},
])

CONV_C = _make_conv("conv-c", "Topic C", [
    {"role": "user", "content": "New topic"},
    {"role": "assistant", "content": "Interesting"},
])

CONV_A_MODIFIED = _make_conv("conv-a", "Topic A", [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there"},
    {"role": "user", "content": "Follow up"},
    {"role": "assistant", "content": "Sure thing"},
])


class TestComputeDiff:
    def test_identical_files(self, tmp_path: Path):
        old = tmp_path / "old.jsonl"
        new = tmp_path / "new.jsonl"
        _write_jsonl(old, [CONV_A, CONV_B])
        _write_jsonl(new, [CONV_A, CONV_B])

        result = compute_diff(old, new)
        assert result.unchanged == 2
        assert result.added == []
        assert result.removed == []
        assert result.changed == []

    def test_added_conversations(self, tmp_path: Path):
        old = tmp_path / "old.jsonl"
        new = tmp_path / "new.jsonl"
        _write_jsonl(old, [CONV_A])
        _write_jsonl(new, [CONV_A, CONV_B, CONV_C])

        result = compute_diff(old, new)
        assert len(result.added) == 2
        assert result.unchanged == 1

    def test_removed_conversations(self, tmp_path: Path):
        old = tmp_path / "old.jsonl"
        new = tmp_path / "new.jsonl"
        _write_jsonl(old, [CONV_A, CONV_B])
        _write_jsonl(new, [CONV_A])

        result = compute_diff(old, new)
        assert len(result.removed) == 1
        assert result.removed[0].conversation_id == "conv-b"

    def test_changed_conversations(self, tmp_path: Path):
        old = tmp_path / "old.jsonl"
        new = tmp_path / "new.jsonl"
        _write_jsonl(old, [CONV_A, CONV_B])
        _write_jsonl(new, [CONV_A_MODIFIED, CONV_B])

        result = compute_diff(old, new)
        assert len(result.changed) == 1
        old_conv, new_conv = result.changed[0]
        assert old_conv.message_count == 2
        assert new_conv.message_count == 4

    def test_all_changes_combined(self, tmp_path: Path):
        old = tmp_path / "old.jsonl"
        new = tmp_path / "new.jsonl"
        _write_jsonl(old, [CONV_A, CONV_B])
        _write_jsonl(new, [CONV_A_MODIFIED, CONV_C])

        result = compute_diff(old, new)
        assert len(result.added) == 1
        assert len(result.removed) == 1
        assert len(result.changed) == 1
        assert result.unchanged == 0


class TestDiffCLI:
    def test_diff_no_bundle(self, tmp_path: Path):
        result = runner.invoke(app, ["diff", "openai", "--out", str(tmp_path)])
        assert result.exit_code == 1

    def test_diff_no_provider(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_path)])
        result = runner.invoke(app, ["diff", "nonexistent", "--out", str(tmp_path)])
        assert result.exit_code == 1

    def test_diff_single_run(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_path)])
        result = runner.invoke(app, ["diff", "openai", "--out", str(tmp_path)])
        assert result.exit_code == 1
        assert "Nur ein Export" in result.output or "Nur ein Export" in (result.stderr or "")

    def test_diff_two_runs(self, openai_zip: Path, tmp_path: Path):
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_path)])
        runner.invoke(app, ["extract", "openai", str(openai_zip), "--out", str(tmp_path), "--force"])
        result = runner.invoke(app, ["diff", "openai", "--out", str(tmp_path)])
        assert result.exit_code == 0
        assert "Unchanged" in result.output

    def test_diff_shows_help(self):
        result = runner.invoke(app, ["--help"])
        assert "diff" in result.output
