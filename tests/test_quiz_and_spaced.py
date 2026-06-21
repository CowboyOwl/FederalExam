from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from federal_exam.database import (
    get_connection,
    get_due_reviews,
    get_failed_history,
    init_db,
    record_attempt,
    upsert_question,
)
from federal_exam.spaced_repetition import ReviewState, next_review_state


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
    "statut_revision": "valide",
    "tags": "tag",
}


def test_failed_attempt_is_stored_and_due(tmp_path: Path):
    db_path = tmp_path / "quiz.db"
    init_db(db_path)
    with get_connection(db_path) as db:
        upsert_question(db, QUESTION)
        question_id = db.execute("SELECT id FROM questions").fetchone()["id"]
        record_attempt(db, question_id, selected_answer="B", is_correct=False, mode="entrainement")
        failures = get_failed_history(db)
        due = get_due_reviews(db)
    assert len(failures) == 1
    assert failures[0]["selected_answer"] == "B"
    assert len(due) == 1


def test_correct_answer_increases_review_interval():
    today = date.today()
    first = next_review_state(ReviewState(), is_correct=True, today=today)
    second = next_review_state(
        ReviewState(
            repetitions=first["repetitions"],
            interval_days=first["interval_days"],
            ease_factor=first["ease_factor"],
        ),
        is_correct=True,
        today=today,
    )
    assert first["due_at"] == (today + timedelta(days=1)).isoformat()
    assert second["due_at"] == (today + timedelta(days=6)).isoformat()
