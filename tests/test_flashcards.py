from __future__ import annotations

import csv
from pathlib import Path

from app import create_app
from federal_exam.database import get_connection, init_db
from federal_exam.flashcards import (
    browse_flashcards,
    get_due_flashcards,
    get_flashcard_history,
    import_flashcards_file,
    record_flashcard_review,
)
from scripts.generate_flashcards import build_flashcards


def test_flashcard_generation_from_notes_has_more_than_10000_cards():
    rows = build_flashcards()
    assert len(rows) > 10000
    for row in rows[:100]:
        assert row["front"].strip()
        assert row["back"].strip()
        assert row["source"].strip()
        assert int(row["page"]) >= 1


def test_generated_flashcard_csv_is_complete():
    path = Path("data") / "generated_flashcards_fr.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) > 10000
    for row in rows:
        assert row["front"].strip()
        assert row["back"].strip()
        assert row["source"].strip()
        assert row["page"].strip()


def test_flashcard_import_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "cards.db"
    init_db(db_path)
    with get_connection(db_path) as db:
        first = import_flashcards_file(db, Path("data") / "generated_flashcards_fr.csv")
        second = import_flashcards_file(db, Path("data") / "generated_flashcards_fr.csv")
        count = db.execute("SELECT COUNT(*) AS total FROM flashcards").fetchone()["total"]
    assert first.inserted > 10000
    assert second.inserted == 0
    assert second.updated == first.inserted
    assert count == first.inserted


def test_review_grades_update_state_and_history(tmp_path: Path):
    db_path = tmp_path / "review.db"
    init_db(db_path)
    with get_connection(db_path) as db:
        import_flashcards_file(db, Path("data") / "generated_flashcards_fr.csv")
        card = get_due_flashcards(db, limit=1)[0]
        record_flashcard_review(db, card["id"], "good")
        state = db.execute(
            "SELECT repetitions, interval_days, ease_factor, due_at FROM flashcard_review_state WHERE flashcard_id = ?",
            (card["id"],),
        ).fetchone()
        history = get_flashcard_history(db, card["id"])
    assert state["repetitions"] == 1
    assert state["interval_days"] == 1
    assert history[0]["grade"] == "good"


def test_again_resets_due_card(tmp_path: Path):
    db_path = tmp_path / "again.db"
    init_db(db_path)
    with get_connection(db_path) as db:
        import_flashcards_file(db, Path("data") / "generated_flashcards_fr.csv")
        card = get_due_flashcards(db, limit=1)[0]
        record_flashcard_review(db, card["id"], "easy")
        record_flashcard_review(db, card["id"], "again")
        due = get_due_flashcards(db, limit=5)
    assert any(item["id"] == card["id"] for item in due)


def test_flashcard_browse_and_routes(tmp_path: Path):
    db_path = tmp_path / "routes.db"
    app = create_app(database_path=db_path, upload_dir=tmp_path / "uploads")
    with get_connection(db_path) as db:
        import_flashcards_file(db, Path("data") / "generated_flashcards_fr.csv")
        cards = browse_flashcards(db, query="ALVESCO", limit=5)
        card_id = cards[0]["id"]

    assert cards
    client = app.test_client()
    for path in ["/cartes", "/cartes/reviser", "/cartes/parcourir", f"/cartes/{card_id}"]:
        response = client.get(path)
        assert response.status_code == 200, path


def test_flashcard_review_persists_after_app_recreation(tmp_path: Path):
    db_path = tmp_path / "persist.db"
    upload_dir = tmp_path / "uploads"
    app = create_app(database_path=db_path, upload_dir=upload_dir)
    with get_connection(app.config["DATABASE_PATH"]) as db:
        import_flashcards_file(db, Path("data") / "generated_flashcards_fr.csv")
        card = get_due_flashcards(db, limit=1)[0]
        record_flashcard_review(db, card["id"], "hard")

    create_app(database_path=db_path, upload_dir=upload_dir)
    with get_connection(db_path) as db:
        history = get_flashcard_history(db, card["id"])
    assert history
    assert history[0]["grade"] == "hard"
