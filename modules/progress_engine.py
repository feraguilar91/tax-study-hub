from __future__ import annotations

from modules.flashcards import (
    record_result as _record_result,
    record_view as _record_view,
    set_confidence as _set_confidence,
)
from modules.session_engine import (
    record_card_view as _record_session_card_view,
    record_quiz_answer as _record_session_quiz_answer,
    record_review as _record_session_review,
)

VALID_CONFIDENCE_VALUES = {
    "Again",
    "Hard",
    "Good",
    "Easy",
}


def record_view(
    card_id: int,
    session_id: int | None = None,
) -> None:
    """Record a card view and optionally update a study session."""

    _record_view(card_id)

    if session_id is not None:
        _record_session_card_view(session_id)


def record_result(
    card_id: int,
    correct: bool,
    session_id: int | None = None,
) -> None:
    """Record a quiz result and optionally update a study session."""

    _record_result(card_id, correct)

    if session_id is not None:
        _record_session_quiz_answer(session_id)


def record_review(
    card_id: int,
    confidence: str,
    session_id: int | None = None,
) -> None:
    """Record a confidence review and optionally update a study session."""

    if confidence not in VALID_CONFIDENCE_VALUES:
        raise ValueError(
            "Confidence must be one of: "
            f"{', '.join(sorted(VALID_CONFIDENCE_VALUES))}"
        )

    _set_confidence(card_id, confidence)

    if session_id is not None:
        _record_session_review(session_id)


def set_confidence(
    card_id: int,
    confidence: str,
    session_id: int | None = None,
) -> None:
    """Backward-compatible alias for record_review."""

    record_review(
        card_id=card_id,
        confidence=confidence,
        session_id=session_id,
    )