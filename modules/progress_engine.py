from __future__ import annotations

from modules.flashcards import (
    record_result as _record_result,
    record_view as _record_view,
    set_confidence as _set_confidence,
)

VALID_CONFIDENCE_VALUES = {
    "Again",
    "Hard",
    "Good",
    "Easy",
}


def record_view(card_id: int) -> None:
    _record_view(card_id)


def record_result(card_id: int, correct: bool) -> None:
    _record_result(card_id, correct)


def record_review(card_id: int, confidence: str) -> None:
    if confidence not in VALID_CONFIDENCE_VALUES:
        raise ValueError(
            "Confidence must be one of: "
            f"{', '.join(sorted(VALID_CONFIDENCE_VALUES))}"
        )

    _set_confidence(card_id, confidence)


def set_confidence(card_id: int, confidence: str) -> None:
    record_review(card_id, confidence)