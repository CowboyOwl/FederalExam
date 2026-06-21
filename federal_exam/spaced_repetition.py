from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ReviewState:
    repetitions: int = 0
    interval_days: int = 0
    ease_factor: float = 2.5


def next_review_state(current: ReviewState, is_correct: bool, today: date | None = None):
    today = today or date.today()
    if not is_correct:
        return {
            "repetitions": 0,
            "interval_days": 0,
            "ease_factor": max(1.3, current.ease_factor - 0.2),
            "due_at": today.isoformat(),
        }

    repetitions = current.repetitions + 1
    if repetitions == 1:
        interval = 1
    elif repetitions == 2:
        interval = 6
    else:
        interval = max(1, round(current.interval_days * current.ease_factor))

    quality = 5
    ease = current.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease = max(1.3, ease)
    due_at = today + timedelta(days=interval)
    return {
        "repetitions": repetitions,
        "interval_days": interval,
        "ease_factor": ease,
        "due_at": due_at.isoformat(),
    }
