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


QUESTION = {
    "id": "Q1",
    "categorie": "Pharmacie clinique",
    "sous_categorie": "Interactions",
    "difficulte": "moyen",
    "question": "Question?",
    "choix_a": "A",
    "choix_b": "B",
    "choix_c": "C",
    "choix_d": "D",
    "bonne_reponse": "A",
    "explication": "Explication",
    "reference": "Reference",
    "tags": "tag",
}


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


def test_macos_path_uses_application_support(monkeypatch, tmp_path: Path):
    home = tmp_path / "home"
    monkeypatch.delenv("FEDERALEXAM_DATA_DIR", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: home)
    assert get_app_data_dir() == home / "Library" / "Application Support" / "FederalExam"


def test_seed_database_imports_generated_bank_once(tmp_path: Path):
    db_path = tmp_path / "seeded.db"
    seed_path = Path("data") / "generated_questions_fr.csv"

    assert seed_database_if_missing(db_path, seed_path) is True
    assert seed_database_if_missing(db_path, seed_path) is False

    with sqlite3.connect(db_path) as connection:
        total = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        cards = connection.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0]
    assert total == 1000
    assert cards > 10000


def test_category_stats_route_renders(tmp_path: Path):
    from federal_exam.database import get_connection, upsert_question

    db_path = tmp_path / "routes.db"
    app = create_app(database_path=db_path, upload_dir=tmp_path / "uploads")
    with get_connection(db_path) as db:
        upsert_question(db, QUESTION)

    client = app.test_client()
    response = client.get("/statistiques/categorie/Pharmacie%20clinique")
    assert response.status_code == 200
    assert "Pharmacie clinique" in response.get_data(as_text=True)
