from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for

from federal_exam.categories import CATEGORIES, DIFFICULTIES, REVIEW_STATUSES
from federal_exam.database import (
    DATABASE_PATH,
    get_connection,
    get_dashboard_stats,
    get_due_reviews,
    get_failed_history,
    get_question,
    get_questions_for_quiz,
    get_stats_by_category,
    get_stats_by_difficulty,
    init_db,
    record_attempt,
)
from federal_exam.importer import import_questions_file


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"


def create_app(database_path: Path | str = DATABASE_PATH) -> Flask:
    app = Flask(__name__)
    app.secret_key = "local-dev-secret-change-if-shared"
    app.config["DATABASE_PATH"] = str(database_path)
    UPLOAD_DIR.mkdir(exist_ok=True)
    init_db(database_path)

    def conn():
        return get_connection(app.config["DATABASE_PATH"])

    @app.context_processor
    def inject_globals():
        return {
            "categories": CATEGORIES,
            "difficulties": DIFFICULTIES,
            "review_statuses": REVIEW_STATUSES,
        }

    @app.get("/")
    def dashboard():
        with conn() as db:
            stats = get_dashboard_stats(db)
            due = get_due_reviews(db, limit=5)
            weak_categories = get_stats_by_category(db)[:5]
        return render_template(
            "dashboard.html",
            stats=stats,
            due=due,
            weak_categories=weak_categories,
        )

    @app.route("/entrainement", methods=["GET", "POST"])
    def training():
        if request.method == "POST":
            category = request.form.get("categorie") or None
            difficulty = request.form.get("difficulte") or None
            count = int(request.form.get("nombre", "10"))
            with conn() as db:
                questions = get_questions_for_quiz(
                    db,
                    category=category,
                    difficulty=difficulty,
                    count=count,
                )
            if not questions:
                flash("Aucune question ne correspond à ces filtres.", "warning")
                return redirect(url_for("training"))
            return start_quiz("entrainement", questions, timed=False)
        return render_template("training.html")

    @app.route("/examen", methods=["GET", "POST"])
    def exam():
        if request.method == "POST":
            count = int(request.form.get("nombre", "50"))
            minutes = int(request.form.get("minutes", "60"))
            with conn() as db:
                questions = get_questions_for_quiz(db, count=count)
            if not questions:
                flash("Importez d'abord des questions pour lancer un examen blanc.", "warning")
                return redirect(url_for("exam"))
            return start_quiz("examen", questions, timed=True, minutes=minutes)
        return render_template("exam.html")

    @app.get("/revisions")
    def reviews():
        with conn() as db:
            questions = get_due_reviews(db, limit=100)
        return render_template("reviews.html", questions=questions)

    @app.post("/revisions/demarrer")
    def start_reviews():
        with conn() as db:
            questions = get_due_reviews(db, limit=50)
        if not questions:
            flash("Aucune révision n'est due pour le moment.", "success")
            return redirect(url_for("reviews"))
        return start_quiz("revision", questions, timed=False)

    @app.get("/erreurs")
    def errors():
        with conn() as db:
            history = get_failed_history(db)
        return render_template("errors.html", history=history)

    @app.route("/importation", methods=["GET", "POST"])
    def importation():
        report = None
        if request.method == "POST":
            upload = request.files.get("fichier")
            if not upload or not upload.filename:
                flash("Choisissez un fichier CSV ou JSON.", "warning")
                return redirect(url_for("importation"))
            target = UPLOAD_DIR / f"{uuid4().hex}_{Path(upload.filename).name}"
            upload.save(target)
            with conn() as db:
                report = import_questions_file(db, target)
            target.unlink(missing_ok=True)
            if report.inserted or report.updated:
                flash(
                    f"Import terminé: {report.inserted} ajoutées, {report.updated} mises à jour.",
                    "success",
                )
            if report.errors:
                flash(f"{len(report.errors)} ligne(s) rejetée(s).", "warning")
        return render_template("importation.html", report=report)

    @app.get("/statistiques")
    def statistics():
        with conn() as db:
            by_category = get_stats_by_category(db, include_empty=True)
            by_difficulty = get_stats_by_difficulty(db)
            stats = get_dashboard_stats(db)
        return render_template(
            "statistics.html",
            by_category=by_category,
            by_difficulty=by_difficulty,
            stats=stats,
        )

    @app.get("/quiz")
    def quiz():
        quiz_state = session.get("quiz")
        if not quiz_state:
            flash("Aucun questionnaire actif.", "warning")
            return redirect(url_for("dashboard"))
        if quiz_expired(quiz_state):
            flash("Le temps est écoulé.", "warning")
            return redirect(url_for("quiz_result"))
        index = quiz_state["index"]
        ids = quiz_state["question_ids"]
        if index >= len(ids):
            return redirect(url_for("quiz_result"))
        with conn() as db:
            question = get_question(db, ids[index])
        return render_template(
            "quiz.html",
            quiz=quiz_state,
            question=question,
            index=index,
            total=len(ids),
            seconds_remaining=seconds_remaining(quiz_state),
        )

    @app.post("/quiz/repondre")
    def answer_quiz():
        quiz_state = session.get("quiz")
        if not quiz_state:
            flash("Aucun questionnaire actif.", "warning")
            return redirect(url_for("dashboard"))
        if quiz_expired(quiz_state):
            flash("Le temps est écoulé.", "warning")
            return redirect(url_for("quiz_result"))
        selected = request.form.get("reponse")
        ids = quiz_state["question_ids"]
        index = quiz_state["index"]
        if selected not in {"A", "B", "C", "D"} or index >= len(ids):
            flash("Réponse invalide.", "warning")
            return redirect(url_for("quiz"))
        question_id = ids[index]
        with conn() as db:
            question = get_question(db, question_id)
            is_correct = selected == question["correct_answer"]
            record_attempt(
                db,
                question_id=question_id,
                selected_answer=selected,
                is_correct=is_correct,
                mode=quiz_state["mode"],
            )
        quiz_state["answers"].append(
            {
                "question_id": question_id,
                "selected": selected,
                "correct": is_correct,
            }
        )
        quiz_state["index"] += 1
        session["quiz"] = quiz_state
        return redirect(url_for("quiz"))

    @app.get("/quiz/resultat")
    def quiz_result():
        quiz_state = session.get("quiz")
        if not quiz_state:
            return redirect(url_for("dashboard"))
        answers = quiz_state["answers"]
        total = len(quiz_state["question_ids"])
        correct = sum(1 for answer in answers if answer["correct"])
        missed_ids = [answer["question_id"] for answer in answers if not answer["correct"]]
        with conn() as db:
            missed = [get_question(db, question_id) for question_id in missed_ids]
        session.pop("quiz", None)
        return render_template(
            "quiz_result.html",
            mode=quiz_state["mode"],
            total=total,
            correct=correct,
            missed=missed,
        )

    def start_quiz(mode: str, questions: list, timed: bool, minutes: int | None = None):
        session["quiz"] = {
            "mode": mode,
            "question_ids": [question["id"] for question in questions],
            "index": 0,
            "answers": [],
            "timed": timed,
            "minutes": minutes,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        return redirect(url_for("quiz"))

    return app


def seconds_remaining(quiz_state: dict) -> int | None:
    if not quiz_state.get("timed"):
        return None
    started_at = datetime.fromisoformat(quiz_state["started_at"])
    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    return max(0, int((quiz_state["minutes"] * 60) - elapsed))


def quiz_expired(quiz_state: dict) -> bool:
    remaining = seconds_remaining(quiz_state)
    return remaining is not None and remaining <= 0


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
