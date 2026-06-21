from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from federal_exam.categories import CATEGORIES
from federal_exam.spaced_repetition import ReviewState, next_review_state


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "federal_exam.db"


def get_connection(path: Path | str = DATABASE_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(path: Path | str = DATABASE_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                sub_category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                prompt TEXT NOT NULL,
                choice_a TEXT NOT NULL,
                choice_b TEXT NOT NULL,
                choice_c TEXT NOT NULL,
                choice_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL CHECK(correct_answer IN ('A','B','C','D')),
                explanation TEXT NOT NULL,
                reference TEXT NOT NULL,
                review_status TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                selected_answer TEXT NOT NULL CHECK(selected_answer IN ('A','B','C','D')),
                is_correct INTEGER NOT NULL CHECK(is_correct IN (0,1)),
                mode TEXT NOT NULL,
                attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS review_state (
                question_id INTEGER PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
                repetitions INTEGER NOT NULL DEFAULT 0,
                interval_days INTEGER NOT NULL DEFAULT 0,
                ease_factor REAL NOT NULL DEFAULT 2.5,
                due_at TEXT NOT NULL DEFAULT CURRENT_DATE,
                last_reviewed_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
            CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
            CREATE INDEX IF NOT EXISTS idx_attempts_question ON attempts(question_id);
            CREATE INDEX IF NOT EXISTS idx_review_due ON review_state(due_at);
            """
        )


def upsert_question(db: sqlite3.Connection, row: dict) -> str:
    existing = db.execute(
        "SELECT id FROM questions WHERE external_id = ?", (row["id"],)
    ).fetchone()
    db.execute(
        """
        INSERT INTO questions (
            external_id, category, sub_category, difficulty, prompt,
            choice_a, choice_b, choice_c, choice_d, correct_answer,
            explanation, reference, review_status, tags
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(external_id) DO UPDATE SET
            category = excluded.category,
            sub_category = excluded.sub_category,
            difficulty = excluded.difficulty,
            prompt = excluded.prompt,
            choice_a = excluded.choice_a,
            choice_b = excluded.choice_b,
            choice_c = excluded.choice_c,
            choice_d = excluded.choice_d,
            correct_answer = excluded.correct_answer,
            explanation = excluded.explanation,
            reference = excluded.reference,
            review_status = excluded.review_status,
            tags = excluded.tags,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            row["id"],
            row["categorie"],
            row["sous_categorie"],
            row["difficulte"],
            row["question"],
            row["choix_a"],
            row["choix_b"],
            row["choix_c"],
            row["choix_d"],
            row["bonne_reponse"],
            row["explication"],
            row["reference"],
            row["statut_revision"],
            row["tags"],
        ),
    )
    question = db.execute(
        "SELECT id FROM questions WHERE external_id = ?", (row["id"],)
    ).fetchone()
    db.execute(
        """
        INSERT OR IGNORE INTO review_state (question_id, due_at)
        VALUES (?, CURRENT_DATE)
        """,
        (question["id"],),
    )
    return "updated" if existing else "inserted"


def get_question(db: sqlite3.Connection, question_id: int) -> sqlite3.Row:
    return db.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()


def get_questions_for_quiz(
    db: sqlite3.Connection,
    category: str | None = None,
    difficulty: str | None = None,
    count: int = 10,
) -> list[sqlite3.Row]:
    filters = []
    params: list[str | int] = []
    if category:
        filters.append("category = ?")
        params.append(category)
    if difficulty:
        filters.append("difficulty = ?")
        params.append(difficulty)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(max(1, min(count, 200)))
    return db.execute(
        f"SELECT * FROM questions {where} ORDER BY RANDOM() LIMIT ?", params
    ).fetchall()


def get_due_reviews(db: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT q.*, rs.repetitions, rs.interval_days, rs.ease_factor, rs.due_at
        FROM review_state rs
        JOIN questions q ON q.id = rs.question_id
        WHERE rs.due_at <= CURRENT_DATE
        ORDER BY rs.due_at ASC, q.category ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def record_attempt(
    db: sqlite3.Connection,
    question_id: int,
    selected_answer: str,
    is_correct: bool,
    mode: str,
) -> None:
    db.execute(
        """
        INSERT INTO attempts (question_id, selected_answer, is_correct, mode)
        VALUES (?, ?, ?, ?)
        """,
        (question_id, selected_answer, int(is_correct), mode),
    )
    state_row = db.execute(
        "SELECT repetitions, interval_days, ease_factor FROM review_state WHERE question_id = ?",
        (question_id,),
    ).fetchone()
    current = ReviewState(
        repetitions=state_row["repetitions"] if state_row else 0,
        interval_days=state_row["interval_days"] if state_row else 0,
        ease_factor=state_row["ease_factor"] if state_row else 2.5,
    )
    next_state = next_review_state(current, is_correct=is_correct)
    db.execute(
        """
        INSERT INTO review_state (
            question_id, repetitions, interval_days, ease_factor, due_at, last_reviewed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(question_id) DO UPDATE SET
            repetitions = excluded.repetitions,
            interval_days = excluded.interval_days,
            ease_factor = excluded.ease_factor,
            due_at = excluded.due_at,
            last_reviewed_at = excluded.last_reviewed_at
        """,
        (
            question_id,
            next_state["repetitions"],
            next_state["interval_days"],
            next_state["ease_factor"],
            next_state["due_at"],
            date.today().isoformat(),
        ),
    )


def get_failed_history(db: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT
            a.attempted_at,
            a.selected_answer,
            q.correct_answer,
            q.prompt,
            q.category,
            q.sub_category,
            q.difficulty,
            q.explanation,
            q.reference
        FROM attempts a
        JOIN questions q ON q.id = a.question_id
        WHERE a.is_correct = 0
        ORDER BY a.attempted_at DESC
        """
    ).fetchall()


def get_dashboard_stats(db: sqlite3.Connection) -> dict:
    totals = db.execute(
        """
        SELECT
            COUNT(*) AS attempts,
            COALESCE(SUM(is_correct), 0) AS correct
        FROM attempts
        """
    ).fetchone()
    question_count = db.execute("SELECT COUNT(*) AS total FROM questions").fetchone()["total"]
    due_count = db.execute(
        "SELECT COUNT(*) AS total FROM review_state WHERE due_at <= CURRENT_DATE"
    ).fetchone()["total"]
    failed_count = db.execute(
        "SELECT COUNT(*) AS total FROM attempts WHERE is_correct = 0"
    ).fetchone()["total"]
    attempts = totals["attempts"]
    correct = totals["correct"]
    accuracy = round((correct / attempts) * 100, 1) if attempts else 0
    return {
        "questions": question_count,
        "attempts": attempts,
        "correct": correct,
        "accuracy": accuracy,
        "due_reviews": due_count,
        "failed": failed_count,
    }


def get_stats_by_category(
    db: sqlite3.Connection, include_empty: bool = False
) -> list[dict]:
    rows = db.execute(
        """
        SELECT
            q.category,
            COUNT(a.id) AS attempts,
            COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id
        GROUP BY q.category
        """
    ).fetchall()
    mapped = {row["category"]: _stats_row(row) for row in rows}
    if include_empty:
        for category in CATEGORIES:
            mapped.setdefault(
                category,
                {"name": category, "attempts": 0, "correct": 0, "accuracy": 0},
            )
    return sorted(mapped.values(), key=lambda item: (item["accuracy"], -item["attempts"]))


def get_stats_by_difficulty(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        """
        SELECT
            q.difficulty AS category,
            COUNT(a.id) AS attempts,
            COALESCE(SUM(a.is_correct), 0) AS correct
        FROM questions q
        LEFT JOIN attempts a ON a.question_id = q.id
        GROUP BY q.difficulty
        ORDER BY q.difficulty
        """
    ).fetchall()
    return [_stats_row(row) for row in rows]


def _stats_row(row: sqlite3.Row) -> dict:
    attempts = row["attempts"]
    correct = row["correct"]
    return {
        "name": row["category"],
        "attempts": attempts,
        "correct": correct,
        "accuracy": round((correct / attempts) * 100, 1) if attempts else 0,
    }
