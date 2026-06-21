from __future__ import annotations

import os
import sys
from pathlib import Path

from federal_exam.database import get_connection, init_db
from federal_exam.importer import import_questions_file


APP_NAME = "FederalExam"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return base.joinpath(*parts)


def get_app_data_dir() -> Path:
    override = os.environ.get("FEDERALEXAM_DATA_DIR")
    if override:
        return Path(override)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / f".{APP_NAME}"


def get_database_path(app_data_dir: Path | None = None) -> Path:
    return (app_data_dir or get_app_data_dir()) / "federal_exam.db"


def get_upload_dir(app_data_dir: Path | None = None) -> Path:
    return (app_data_dir or get_app_data_dir()) / "uploads"


def seed_database_if_missing(
    database_path: Path | str | None = None,
    seed_csv_path: Path | str | None = None,
) -> bool:
    db_path = Path(database_path) if database_path else get_database_path()
    if db_path.exists():
        return False

    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(db_path)

    seed_path = Path(seed_csv_path) if seed_csv_path else resource_path(
        "data", "generated_questions_fr.csv"
    )
    if not seed_path.exists():
        return True

    with get_connection(db_path) as db:
        report = import_questions_file(db, seed_path)
    if report.errors:
        preview = "; ".join(report.errors[:5])
        raise RuntimeError(f"Import initial incomplet: {preview}")
    return True
