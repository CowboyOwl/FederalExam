from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from federal_exam.flashcards import FLASHCARD_FIELDS
from scripts.generate_draft_questions import NOTES_DIR, balanced_facts, extract_note_facts


OUTPUT = PROJECT_ROOT / "data" / "generated_flashcards_fr.csv"


def build_flashcards() -> list[dict[str, str]]:
    facts = balanced_facts(extract_note_facts(NOTES_DIR))
    rows = []
    for index, fact in enumerate(facts, start=1):
        rows.append(
            {
                "id": f"CARD-{index:05d}",
                "front": f"Que faut-il retenir sur « {fact.topic} » ?",
                "back": f"{fact.text}\n\nSource: {fact.source}, page {fact.page}",
                "categorie": fact.category,
                "sous_categorie": fact.sub_category,
                "source": fact.source,
                "page": str(fact.page),
                "tags": f"notes,{fact.sub_category.lower()},{fact.topic.lower()}",
            }
        )
    return rows


def main() -> int:
    rows = build_flashcards()
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FLASHCARD_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} cartes générées dans {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
