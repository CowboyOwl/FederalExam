from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from federal_exam.categories import CATEGORIES
from federal_exam.spaced_repetition import ReviewState, next_flashcard_state


FLASHCARD_FIELDS = [
    "id",
    "front",
    "back",
    "categorie",
    "sous_categorie",
    "source",
    "page",
    "tags",
]
GRADES = ["again", "hard", "good", "easy"]


@dataclass
class FlashcardImportReport:
    inserted: int = 0
    updated: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def accepted(self) -> int:
        return self.inserted + self.updated


def import_flashcards_file(db: sqlite3.Connection, path: Path | str) -> FlashcardImportReport:
    report = FlashcardImportReport()
    seen_ids: set[str] = set()
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        for index, raw_row in enumerate(rows, start=2):
            row = normalize_flashcard_row(raw_row)
            errors = validate_flashcard_row(row)
            if row.get("id") in seen_ids:
                errors.append("id dupliqué dans le fichier")
            if errors:
                report.errors.append(f"Ligne {index}: {', '.join(errors)}")
                continue
            seen_ids.add(row["id"])
            result = upsert_flashcard(db, row)
            if result == "inserted":
                report.inserted += 1
            else:
                report.updated += 1
    db.commit()
    return report


def normalize_flashcard_row(row: dict) -> dict:
    normalized = {}
    for field in FLASHCARD_FIELDS:
        value = row.get(field, "")
        normalized[field] = str(value).strip() if value is not None else ""
    return normalized


def validate_flashcard_row(row: dict) -> list[str]:
    errors = []
    for field in FLASHCARD_FIELDS:
        if not row.get(field):
            errors.append(f"champ manquant: {field}")
    if row.get("categorie") and row["categorie"] not in CATEGORIES:
        errors.append("catégorie inconnue")
    if row.get("page"):
        try:
            if int(row["page"]) < 1:
                errors.append("page invalide")
        except ValueError:
            errors.append("page invalide")
    return errors


def upsert_flashcard(db: sqlite3.Connection, row: dict) -> str:
    existing = db.execute(
        "SELECT id FROM flashcards WHERE external_id = ?", (row["id"],)
    ).fetchone()
    db.execute(
        """
        INSERT INTO flashcards (
            external_id, front, back, category, sub_category, source, page, tags
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(external_id) DO UPDATE SET
            front = excluded.front,
            back = excluded.back,
            category = excluded.category,
            sub_category = excluded.sub_category,
            source = excluded.source,
            page = excluded.page,
            tags = excluded.tags,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            row["id"],
            row["front"],
            row["back"],
            row["categorie"],
            row["sous_categorie"],
            row["source"],
            int(row["page"]),
            row["tags"],
        ),
    )
    card = db.execute(
        "SELECT id FROM flashcards WHERE external_id = ?", (row["id"],)
    ).fetchone()
    db.execute(
        """
        INSERT OR IGNORE INTO flashcard_review_state (flashcard_id, due_at)
        VALUES (?, CURRENT_DATE)
        """,
        (card["id"],),
    )
    return "updated" if existing else "inserted"


def get_flashcard(db: sqlite3.Connection, card_id: int) -> sqlite3.Row | None:
    return db.execute(
        """
        SELECT c.*, s.repetitions, s.interval_days, s.ease_factor, s.due_at, s.last_reviewed_at
        FROM flashcards c
        JOIN flashcard_review_state s ON s.flashcard_id = c.id
        WHERE c.id = ?
        """,
        (card_id,),
    ).fetchone()


def get_due_flashcards(db: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT c.*, s.repetitions, s.interval_days, s.ease_factor, s.due_at
        FROM flashcard_review_state s
        JOIN flashcards c ON c.id = s.flashcard_id
        WHERE s.due_at <= CURRENT_DATE
        ORDER BY s.due_at ASC, s.repetitions ASC, c.source ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def get_next_due_flashcard(db: sqlite3.Connection) -> sqlite3.Row | None:
    rows = get_due_flashcards(db, limit=1)
    return rows[0] if rows else None


def record_flashcard_review(db: sqlite3.Connection, flashcard_id: int, grade: str) -> None:
    if grade not in GRADES:
        raise ValueError("grade invalide")
    state = db.execute(
        """
        SELECT repetitions, interval_days, ease_factor
        FROM flashcard_review_state
        WHERE flashcard_id = ?
        """,
        (flashcard_id,),
    ).fetchone()
    current = ReviewState(
        repetitions=state["repetitions"] if state else 0,
        interval_days=state["interval_days"] if state else 0,
        ease_factor=state["ease_factor"] if state else 2.5,
    )
    next_state = next_flashcard_state(current, grade)
    db.execute(
        """
        INSERT INTO flashcard_reviews (
            flashcard_id, grade, previous_interval_days, new_interval_days,
            previous_ease_factor, new_ease_factor
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            flashcard_id,
            grade,
            current.interval_days,
            next_state["interval_days"],
            current.ease_factor,
            next_state["ease_factor"],
        ),
    )
    db.execute(
        """
        INSERT INTO flashcard_review_state (
            flashcard_id, repetitions, interval_days, ease_factor, due_at, last_reviewed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(flashcard_id) DO UPDATE SET
            repetitions = excluded.repetitions,
            interval_days = excluded.interval_days,
            ease_factor = excluded.ease_factor,
            due_at = excluded.due_at,
            last_reviewed_at = excluded.last_reviewed_at
        """,
        (
            flashcard_id,
            next_state["repetitions"],
            next_state["interval_days"],
            next_state["ease_factor"],
            next_state["due_at"],
            date.today().isoformat(),
        ),
    )
    db.commit()


def get_flashcard_stats(db: sqlite3.Connection) -> dict:
    total = db.execute("SELECT COUNT(*) AS total FROM flashcards").fetchone()["total"]
    due = db.execute(
        "SELECT COUNT(*) AS total FROM flashcard_review_state WHERE due_at <= CURRENT_DATE"
    ).fetchone()["total"]
    reviewed_today = db.execute(
        "SELECT COUNT(*) AS total FROM flashcard_reviews WHERE date(reviewed_at) = CURRENT_DATE"
    ).fetchone()["total"]
    mature = db.execute(
        "SELECT COUNT(*) AS total FROM flashcard_review_state WHERE interval_days >= 21"
    ).fetchone()["total"]
    weak = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM flashcard_review_state
        WHERE ease_factor < 2.1 OR (repetitions = 0 AND last_reviewed_at IS NOT NULL)
        """
    ).fetchone()["total"]
    return {
        "total": total,
        "due": due,
        "reviewed_today": reviewed_today,
        "mature": mature,
        "weak": weak,
    }


def browse_flashcards(
    db: sqlite3.Connection,
    category: str | None = None,
    source: str | None = None,
    due_only: bool = False,
    query: str | None = None,
    limit: int = 200,
) -> list[sqlite3.Row]:
    filters = []
    params: list[str | int] = []
    if category:
        filters.append("c.category = ?")
        params.append(category)
    if source:
        filters.append("c.source = ?")
        params.append(source)
    if due_only:
        filters.append("s.due_at <= CURRENT_DATE")
    if query:
        filters.append("(c.front LIKE ? OR c.back LIKE ? OR c.tags LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like, like])
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(limit)
    return db.execute(
        f"""
        SELECT c.*, s.repetitions, s.interval_days, s.ease_factor, s.due_at
        FROM flashcards c
        JOIN flashcard_review_state s ON s.flashcard_id = c.id
        {where}
        ORDER BY c.source ASC, c.page ASC, c.id ASC
        LIMIT ?
        """,
        params,
    ).fetchall()


def get_flashcard_sources(db: sqlite3.Connection) -> list[str]:
    rows = db.execute("SELECT DISTINCT source FROM flashcards ORDER BY source").fetchall()
    return [row["source"] for row in rows]


def get_flashcard_history(db: sqlite3.Connection, card_id: int) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT *
        FROM flashcard_reviews
        WHERE flashcard_id = ?
        ORDER BY reviewed_at DESC
        LIMIT 50
        """,
        (card_id,),
    ).fetchall()
