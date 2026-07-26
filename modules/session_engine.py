from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from modules.database import connect


def _utc_now() -> str:
    """Return the current UTC time in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def start_session() -> int:
    """Create a new study session and return its database ID."""

    started_at = _utc_now()

    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO study_sessions (
                started_at,
                updated_at
            )
            VALUES (?, ?)
            """,
            (
                started_at,
                started_at,
            ),
        )

        session_id = cursor.lastrowid

    if session_id is None:
        raise RuntimeError("Unable to create study session.")

    return int(session_id)


def get_session(session_id: int) -> dict[str, Any] | None:
    """Return one study session as a dictionary."""

    with connect() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                started_at,
                ended_at,
                duration_seconds,
                cards_viewed,
                quiz_answers,
                reviews,
                created_at,
                updated_at
            FROM study_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    return dict(row) if row else None


def end_session(session_id: int) -> None:
    """End a session and store its duration."""

    session = get_session(session_id)

    if session is None:
        raise ValueError(f"Study session {session_id} does not exist.")

    if session["ended_at"] is not None:
        return

    ended_at = datetime.now(timezone.utc)
    started_at = datetime.fromisoformat(session["started_at"])

    duration_seconds = max(
        0,
        int((ended_at - started_at).total_seconds()),
    )

    ended_at_text = ended_at.isoformat()

    with connect() as connection:
        connection.execute(
            """
            UPDATE study_sessions
            SET
                ended_at = ?,
                duration_seconds = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                ended_at_text,
                duration_seconds,
                ended_at_text,
                session_id,
            ),
        )


def record_card_view(session_id: int) -> None:
    """Increment the number of cards viewed in a session."""

    _increment_session_counter(
        session_id=session_id,
        column_name="cards_viewed",
    )


def record_quiz_answer(session_id: int) -> None:
    """Increment the number of quiz answers in a session."""

    _increment_session_counter(
        session_id=session_id,
        column_name="quiz_answers",
    )


def record_review(session_id: int) -> None:
    """Increment the number of flashcard reviews in a session."""

    _increment_session_counter(
        session_id=session_id,
        column_name="reviews",
    )


def _increment_session_counter(
    session_id: int,
    column_name: str,
) -> None:
    """Increment one approved session counter."""

    allowed_columns = {
        "cards_viewed",
        "quiz_answers",
        "reviews",
    }

    if column_name not in allowed_columns:
        raise ValueError(f"Invalid session counter: {column_name}")

    updated_at = _utc_now()

    with connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE study_sessions
            SET
                {column_name} = {column_name} + 1,
                updated_at = ?
            WHERE id = ?
              AND ended_at IS NULL
            """,
            (
                updated_at,
                session_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Active study session {session_id} was not found."
            )