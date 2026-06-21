from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_draft_questions import NOTES_DIR, extract_note_facts


def main() -> int:
    facts = extract_note_facts(NOTES_DIR)
    print(f"{len(facts)} faits extraits")
    for fact in facts[:50]:
        print(f"{fact.source}, page {fact.page}: {fact.text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
