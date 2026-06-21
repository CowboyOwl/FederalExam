from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from federal_exam.categories import ANSWER_KEYS, CATEGORIES, DIFFICULTIES
from federal_exam.database import upsert_question


REQUIRED_FIELDS = [
    "id",
    "categorie",
    "sous_categorie",
    "difficulte",
    "question",
    "choix_a",
    "choix_b",
    "choix_c",
    "choix_d",
    "bonne_reponse",
    "explication",
    "reference",
    "tags",
]


@dataclass
class ImportReport:
    inserted: int = 0
    updated: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def accepted(self) -> int:
        return self.inserted + self.updated


def import_questions_file(db: sqlite3.Connection, path: Path | str) -> ImportReport:
    path = Path(path)
    rows = _read_rows(path)
    report = ImportReport()
    seen_ids: set[str] = set()
    for index, raw_row in enumerate(rows, start=2):
        row = _normalize_row(raw_row)
        errors = validate_question_row(row)
        if row.get("id") in seen_ids:
            errors.append("id dupliqué dans le fichier")
        if errors:
            report.errors.append(f"Ligne {index}: {', '.join(errors)}")
            continue
        seen_ids.add(row["id"])
        result = upsert_question(db, row)
        if result == "inserted":
            report.inserted += 1
        else:
            report.updated += 1
    db.commit()
    return report


def validate_question_row(row: dict) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            errors.append(f"champ manquant: {field}")
    if row.get("categorie") and row["categorie"] not in CATEGORIES:
        errors.append("catégorie inconnue")
    if row.get("difficulte") and row["difficulte"] not in DIFFICULTIES:
        errors.append("difficulté invalide")
    if row.get("bonne_reponse") and row["bonne_reponse"] not in ANSWER_KEYS:
        errors.append("bonne_reponse doit valoir A, B, C ou D")
    return errors


def _read_rows(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            payload = payload.get("questions", [])
        if not isinstance(payload, list):
            raise ValueError("Le JSON doit être une liste ou contenir une clé 'questions'.")
        return payload
    raise ValueError("Format non pris en charge. Utilisez CSV ou JSON.")


def _normalize_row(row: dict) -> dict:
    normalized = {}
    for field in REQUIRED_FIELDS:
        value = row.get(field, "")
        normalized[field] = str(value).strip() if value is not None else ""
    normalized["bonne_reponse"] = normalized["bonne_reponse"].upper()
    normalized["difficulte"] = normalized["difficulte"].lower()
    return normalized
