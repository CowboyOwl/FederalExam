from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from federal_exam.database import get_connection, init_db
from federal_exam.flashcards import import_flashcards_file
from federal_exam.runtime import get_database_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Importer une banque de cartes mémoire.")
    parser.add_argument("file", type=Path, help="Fichier CSV de cartes mémoire")
    parser.add_argument("--db", type=Path, default=get_database_path(), help="Base SQLite cible")
    args = parser.parse_args()

    init_db(args.db)
    with get_connection(args.db) as db:
        report = import_flashcards_file(db, args.file)

    print(f"Ajoutées: {report.inserted}")
    print(f"Mises à jour: {report.updated}")
    print(f"Rejetées: {len(report.errors)}")
    for error in report.errors[:20]:
        print(f"- {error}")
    if len(report.errors) > 20:
        print(f"... {len(report.errors) - 20} erreurs supplémentaires")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
