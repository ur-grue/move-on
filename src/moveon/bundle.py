from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from moveon.exceptions import BundleError, ManifestError
from moveon.models import Manifest, ManifestRun


BUNDLE_DIR = "MOVEON.d"
MANIFEST_FILE = "manifest.json"


def bundle_path(out_dir: Path) -> Path:
    return out_dir / BUNDLE_DIR


def ensure_bundle(out_dir: Path) -> Path:
    bp = bundle_path(out_dir)
    bp.mkdir(mode=0o700, parents=True, exist_ok=True)
    _ensure_inner_gitignore(bp)
    return bp


def _ensure_inner_gitignore(bp: Path) -> None:
    gitignore = bp / ".gitignore"
    if not gitignore.exists():
        _write_secure(gitignore, "*\n")


def _write_secure(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o600)


def ensure_provider_dir(bp: Path, provider: str) -> Path:
    raw_dir = bp / "raw" / provider
    raw_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return raw_dir


def ensure_erase_dir(bp: Path) -> Path:
    erase_dir = bp / "erase"
    erase_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return erase_dir


def read_manifest(bp: Path) -> Manifest:
    manifest_path = bp / MANIFEST_FILE
    if not manifest_path.exists():
        return Manifest()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return Manifest.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        raise ManifestError(f"Corrupt manifest: {e}") from e


def write_manifest(bp: Path, manifest: Manifest) -> None:
    data = manifest.model_dump(mode="json")
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    manifest_path = bp / MANIFEST_FILE
    _write_atomic(manifest_path, content)


def _write_atomic(target: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(tmp, 0o600)
        shutil.move(tmp, target)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_jsonl(bp: Path, provider: str, lines: list[str], manifest: Manifest) -> Path:
    provider_dir = ensure_provider_dir(bp, provider)
    target = provider_dir / "messages.jsonl"

    pm = manifest.providers.get(provider)
    if pm and pm.runs:
        old_index = pm.active_run
        archive_name = f"messages-run-{old_index}.jsonl"
        archive_path = provider_dir / archive_name
        if target.exists():
            shutil.move(str(target), str(archive_path))

    content = "\n".join(lines) + "\n" if lines else ""
    _write_atomic(target, content)
    return target


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_string(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def check_git_warnings(bp: Path) -> None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=bp,
        )
        if result.returncode != 0:
            return

        repo_root = Path(result.stdout.strip())
        gitignore_path = repo_root / ".gitignore"

        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
            bundle_rel = os.path.relpath(bp, repo_root)
            if BUNDLE_DIR in content or bundle_rel in content:
                return

        print(
            f"Warning: {BUNDLE_DIR}/ is inside a git repo but not in .gitignore. "
            "Your chat history could be accidentally committed.",
            file=sys.stderr,
        )
    except (OSError, FileNotFoundError):
        pass


def print_extraction_warning() -> None:
    print(
        f"⚠ {BUNDLE_DIR}/raw/ contains your chat history in plaintext. "
        "Do not commit to git or store in cloud-synced folders.",
        file=sys.stderr,
    )
