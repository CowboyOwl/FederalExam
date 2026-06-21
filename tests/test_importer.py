from __future__ import annotations

from pathlib import Path

from federal_exam.database import get_connection, init_db
from federal_exam.importer import import_questions_file, validate_question_row


def test_import_valid_csv(tmp_path: Path):
    db_path = tmp_path / "test.db"
    csv_path = tmp_path / "questions.csv"
    csv_path.write_text(
        "id,categorie,sous_categorie,difficulte,question,choix_a,choix_b,choix_c,choix_d,bonne_reponse,explication,reference,tags\n"
        "Q1,Droit pharmaceutique suisse,LPTh,facile,Question?,A,B,C,D,B,Explication,Reference,tag\n",
        encoding="utf-8",
    )
    init_db(db_path)
    with get_connection(db_path) as db:
        report = import_questions_file(db, csv_path)
        count = db.execute("SELECT COUNT(*) AS total FROM questions").fetchone()["total"]
    assert report.inserted == 1
    assert report.errors == []
    assert count == 1


def test_reject_invalid_answer():
    row = {
        "id": "Q1",
        "categorie": "Droit pharmaceutique suisse",
        "sous_categorie": "LPTh",
        "difficulte": "facile",
        "question": "Question?",
        "choix_a": "A",
        "choix_b": "B",
        "choix_c": "C",
        "choix_d": "D",
        "bonne_reponse": "E",
        "explication": "Explication",
        "reference": "Reference",
        "tags": "tag",
    }
    errors = validate_question_row(row)
    assert "bonne_reponse doit valoir A, B, C ou D" in errors


def test_import_handles_more_than_1000_rows(tmp_path: Path):
    db_path = tmp_path / "large.db"
    csv_path = tmp_path / "large.csv"
    header = "id,categorie,sous_categorie,difficulte,question,choix_a,choix_b,choix_c,choix_d,bonne_reponse,explication,reference,tags\n"
    rows = [
        f"Q{i},Pharmacie clinique,Sous,moyen,Question {i}?,A,B,C,D,A,Explication,Reference,tag\n"
        for i in range(1001)
    ]
    csv_path.write_text(header + "".join(rows), encoding="utf-8")
    init_db(db_path)
    with get_connection(db_path) as db:
        report = import_questions_file(db, csv_path)
        count = db.execute("SELECT COUNT(*) AS total FROM questions").fetchone()["total"]
    assert report.accepted == 1001
    assert count == 1001


def test_legacy_status_column_is_ignored(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    csv_path = tmp_path / "legacy.csv"
    csv_path.write_text(
        "id,categorie,sous_categorie,difficulte,question,choix_a,choix_b,choix_c,choix_d,bonne_reponse,explication,reference,statut_revision,tags\n"
        "Q1,Pharmacie clinique,Sous,moyen,Question?,A,B,C,D,A,Explication,Reference,a_verifier,tag\n",
        encoding="utf-8",
    )
    init_db(db_path)
    with get_connection(db_path) as db:
        report = import_questions_file(db, csv_path)
        status = db.execute("SELECT review_status FROM questions").fetchone()["review_status"]
    assert report.accepted == 1
    assert report.errors == []
    assert status == "active"
