from __future__ import annotations

import sqlite3
from pathlib import Path

from app import create_app
from federal_exam.runtime import (
    get_app_data_dir,
    get_database_path,
    get_upload_dir,
    seed_database_if_missing,
)


def test_create_app_uses_requested_database_path(tmp_path: Path):
    db_path = tmp_path / "custom.db"
    app = create_app(database_path=db_path, upload_dir=tmp_path / "uploads")
    assert app.config["DATABASE_PATH"] == str(db_path)
    assert db_path.exists()


def test_default_paths_use_local_app_data(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("FEDERALEXAM_DATA_DIR", raising=False)

    app_data = get_app_data_dir()
    assert app_data == tmp_path / "FederalExam"
    assert get_database_path() == app_data / "federal_exam.db"
    assert get_upload_dir() == app_data / "uploads"


def test_data_dir_override_wins(monkeypatch, tmp_path: Path):
    override = tmp_path / "portable-data"
    monkeypatch.setenv("FEDERALEXAM_DATA_DIR", str(override))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "ignored"))
    assert get_app_data_dir() == override


def test_seed_database_imports_generated_bank_once(tmp_path: Path):
    db_path = tmp_path / "seeded.db"
    seed_path = Path("data") / "generated_questions_fr.csv"

    assert seed_database_if_missing(db_path, seed_path) is True
    assert seed_database_if_missing(db_path, seed_path) is False

    with sqlite3.connect(db_path) as connection:
        total = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    assert total == 1000
