from __future__ import annotations

import csv
from pathlib import Path

from federal_exam.database import get_connection, init_db
from federal_exam.importer import import_questions_file


def test_generated_bank_has_1000_active_questions():
    path = Path("data") / "generated_questions_fr.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1000
    assert "statut_revision" not in rows[0]
    assert not any("a_verifier" in str(row) or "brouillon" in str(row) for row in rows)
    for row in rows:
        for field in [
            "question",
            "choix_a",
            "choix_b",
            "choix_c",
            "choix_d",
            "bonne_reponse",
            "explication",
            "reference",
        ]:
            assert row[field].strip()


def test_generated_bank_imports(tmp_path: Path):
    db_path = tmp_path / "generated.db"
    init_db(db_path)
    with get_connection(db_path) as db:
        report = import_questions_file(db, Path("data") / "generated_questions_fr.csv")
        count = db.execute("SELECT COUNT(*) AS total FROM questions").fetchone()["total"]
    assert report.accepted == 1000
    assert report.errors == []
    assert count == 1000
