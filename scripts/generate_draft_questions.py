from __future__ import annotations

import csv
import hashlib
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from federal_exam.categories import CATEGORIES
from federal_exam.importer import REQUIRED_FIELDS


NOTES_DIR = PROJECT_ROOT / "notes"
OUTPUT = PROJECT_ROOT / "data" / "generated_questions_fr.csv"
TARGET_COUNT = 1000

DIFFICULTIES = ["facile", "moyen", "difficile", "moyen", "facile"]
ANSWER_KEYS = ["A", "B", "C", "D"]

FILE_CATEGORY_HINTS = {
    "ASTHME": "Pharmacologie et thérapeutique",
    "BPCO": "Pharmacologie et thérapeutique",
    "COEUR": "Pharmacologie et thérapeutique",
    "CIRCU": "Pharmacologie et thérapeutique",
    "DERMATO": "Pharmacie clinique",
    "ESTOMAC": "Pharmacologie et thérapeutique",
    "INTESTINS": "Pharmacologie et thérapeutique",
    "GYNECOLOGIE": "Pharmacie clinique",
    "METABO": "Pharmacologie et thérapeutique",
    "OPHTA": "Pharmacie clinique",
    "ORL": "Pharmacie clinique",
    "SANG": "Pharmacologie et thérapeutique",
    "SNC": "Pharmacologie et thérapeutique",
    "UROLOGIE": "Pharmacie clinique",
    "MEDICAMENTS": "Pharmacologie et thérapeutique",
}

QUESTION_TEMPLATES = [
    "Selon les notes, quel énoncé est associé à « {topic} » ?",
    "Dans les notes, quelle affirmation correspond le mieux à « {topic} » ?",
    "Quel point faut-il retenir à propos de « {topic} » ?",
    "Quelle proposition reprend correctement les notes sur « {topic} » ?",
]


@dataclass(frozen=True)
class NoteFact:
    text: str
    source: str
    page: int
    category: str
    sub_category: str
    topic: str


def main() -> int:
    facts = extract_note_facts(NOTES_DIR)
    if len(facts) < 4:
        raise SystemExit("Extraction insuffisante: vérifiez le dossier notes/ et pypdf.")

    rows = build_questions(facts, TARGET_COUNT)
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} questions générées depuis {len(facts)} faits extraits dans {OUTPUT}")
    return 0


def extract_note_facts(notes_dir: Path) -> list[NoteFact]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit(
            "pypdf est requis. Installez-le avec: python -m pip install -r requirements-build.txt"
        ) from exc

    facts: list[NoteFact] = []
    seen: set[str] = set()
    for pdf_path in sorted(notes_dir.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        for page_index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            for sentence in split_facts(text):
                key = dedupe_key(sentence, pdf_path.name)
                if key in seen:
                    continue
                seen.add(key)
                category = category_for_file(pdf_path.name)
                facts.append(
                    NoteFact(
                        text=sentence,
                        source=pdf_path.name,
                        page=page_index,
                        category=category,
                        sub_category=subcategory_for_file(pdf_path.name),
                        topic=topic_from_text(sentence),
                    )
                )
    return facts


def split_facts(text: str) -> list[str]:
    text = normalize_spacing(text)
    pieces = re.split(r"(?<=[.!?])\s+|(?:\s+[•\-]\s+)|(?:\s{2,})", text)
    facts = []
    for piece in pieces:
        cleaned = clean_fact(piece)
        if is_useful_fact(cleaned):
            facts.append(cleaned)
    return facts


def clean_fact(text: str) -> str:
    text = normalize_spacing(text)
    text = re.sub(r".*?Angelica Monti Cavalli review 2026\s+", "", text, flags=re.I)
    text = re.sub(r".*?Monti Cavalli Angelica review 2026\s+", "", text, flags=re.I)
    text = re.sub(r"^Fiches\s+.+?EXAMEN FEDERAL 2026\s+", "", text, flags=re.I)
    text = re.sub(r"^[\W\d_]+", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip(" -•\t\r\n")


def is_useful_fact(text: str) -> bool:
    if len(text) < 35 or len(text) > 260:
        return False
    if text.count(" ") < 4:
        return False
    if re.search(r"https?://|www\.|@|\.(com|ch|org)\b", text, re.I):
        return False
    folded = strip_accents(text).upper()
    if "EXAMEN FEDERAL" in folded or "ANGELICA MONTI" in folded or "MONTI CAVALLI" in folded:
        return False
    letters = sum(char.isalpha() for char in text)
    return letters / max(1, len(text)) > 0.55


def dedupe_key(text: str, source_name: str) -> str:
    normalized = strip_accents(text).lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    words = normalized.split()
    if "medicaments federal" in strip_accents(source_name).lower():
        words = [word for word in words if len(word) > 3]
    return " ".join(words[:36])


def build_questions(facts: list[NoteFact], target_count: int) -> list[dict[str, str]]:
    ordered_facts = balanced_facts(facts)
    rows = []
    for index in range(target_count):
        fact = ordered_facts[index % len(ordered_facts)]
        distractors = choose_distractors(ordered_facts, index, fact)
        choices, correct_key = rotate_answers(fact.text, distractors, index)
        template = QUESTION_TEMPLATES[index % len(QUESTION_TEMPLATES)]
        rows.append(
            {
                "id": f"NOTE-{index + 1:04d}",
                "categorie": fact.category,
                "sous_categorie": fact.sub_category,
                "difficulte": DIFFICULTIES[index % len(DIFFICULTIES)],
                "question": template.format(topic=fact.topic),
                "choix_a": choices["A"],
                "choix_b": choices["B"],
                "choix_c": choices["C"],
                "choix_d": choices["D"],
                "bonne_reponse": correct_key,
                "explication": fact.text,
                "reference": f"{fact.source}, page {fact.page}",
                "tags": f"notes,{fact.sub_category.lower()},{fact.topic.lower()}",
            }
        )
    return rows


def balanced_facts(facts: list[NoteFact]) -> list[NoteFact]:
    groups: dict[str, list[NoteFact]] = {}
    for fact in facts:
        groups.setdefault(fact.source, []).append(fact)

    ordered = []
    sources = sorted(groups)
    max_length = max(len(items) for items in groups.values())
    for offset in range(max_length):
        for source in sources:
            items = groups[source]
            if offset < len(items):
                ordered.append(items[offset])
    return ordered


def choose_distractors(facts: list[NoteFact], index: int, fact: NoteFact) -> list[str]:
    distractors = []
    cursor = index + 7
    while len(distractors) < 3:
        candidate = facts[cursor % len(facts)].text
        cursor += 11
        if candidate != fact.text and candidate not in distractors:
            distractors.append(candidate)
    return distractors


def rotate_answers(correct: str, distractors: list[str], seed: int) -> tuple[dict[str, str], str]:
    answers = [correct, *distractors[:3]]
    rotation = seed % 4
    answers = answers[rotation:] + answers[:rotation]
    choices = dict(zip(ANSWER_KEYS, answers))
    correct_key = next(key for key, value in choices.items() if value == correct)
    return choices, correct_key


def topic_from_text(text: str) -> str:
    candidates = re.findall(r"\b[A-ZÉÈÀÂÊÎÔÛÄËÏÖÜÇ][\wÉéÈèÀàÂâÊêÎîÔôÛûÄäËëÏïÖöÜüÇç'’-]{3,}\b", text)
    if candidates:
        return " ".join(candidates[:3])[:80]
    words = [word for word in re.findall(r"[\wÉéÈèÀàÂâÊêÎîÔôÛûÄäËëÏïÖöÜüÇç'’-]+", text) if len(word) > 4]
    return " ".join(words[:4])[:80] or "ce point"


def category_for_file(name: str) -> str:
    folded = strip_accents(name).upper()
    for marker, category in FILE_CATEGORY_HINTS.items():
        if marker in folded:
            return category
    return CATEGORIES[0]


def subcategory_for_file(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"^FICHES\s+", "", stem, flags=re.I)
    stem = stem.replace("Médicaments Fédéral 2026 - Résumés.pptx", "Médicaments")
    return normalize_spacing(stem).title()


def normalize_spacing(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def strip_accents(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )


if __name__ == "__main__":
    raise SystemExit(main())
