from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def openai_zip(fixtures_dir: Path) -> Path:
    return fixtures_dir / "openai-sample.zip"


@pytest.fixture
def anthropic_zip(fixtures_dir: Path) -> Path:
    return fixtures_dir / "anthropic-sample.zip"


@pytest.fixture
def corrupt_zip(fixtures_dir: Path) -> Path:
    return fixtures_dir / "corrupt.zip"


@pytest.fixture
def google_zip(fixtures_dir: Path) -> Path:
    return fixtures_dir / "google-sample.zip"


@pytest.fixture
def meta_zip(fixtures_dir: Path) -> Path:
    return fixtures_dir / "meta-sample.zip"


@pytest.fixture
def wrong_format_zip(fixtures_dir: Path) -> Path:
    return fixtures_dir / "wrong-format.zip"


@pytest.fixture
def tmp_bundle(tmp_path: Path) -> Path:
    return tmp_path
