from __future__ import annotations

from datetime import datetime, timedelta

from modules.database import connect, initialize_database


def get_filter_options() -> tuple[list[str], list[str]]:
    initialize_database()

    with connect() as connection:
        parts = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT exam_part
                FROM flashcards
                ORDER BY exam_part
                """
            )
        ]

        topics = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT topic
                FROM flashcards
                ORDER BY topic
                """
            )
        ]

    return parts, topics


def get_cards(
    exam_part: str | None = None,
    topic: str | None = None,
    search: str | None = None,
    bookmarked_only: bool = False,
    due_only: bool = False,
    weak_only: bool = False,
) -> list[dict]:
    initialize_database()

    conditions: list[str] = []
    parameters: list[object] = []

    if exam_part and exam_part != "All":
        conditions.append("f.exam_part = ?")
        parameters.append(exam_part)

    if topic and topic != "All":
        conditions.append("f.topic = ?")
        parameters.append(topic)

    if search:
        conditions.append(
            """
            (
                f.question LIKE ?
                OR f.answer LIKE ?
                OR f.topic LIKE ?
            )
            """
        )
        pattern = f"%{search}%"
        parameters.extend([pattern, pattern, pattern])

    if bookmarked_only:
        conditions.append("COALESCE(p.is_bookmarked, 0) = 1")

    if due_only:
        conditions.append(
            """
            (
                p.next_review_at IS NULL
                OR datetime(p.next_review_at) <= datetime('now')
            )
            """
        )

    if weak_only:
        conditions.append(
            "COALESCE(p.confidence, '') IN ('Again', 'Hard')"
        )

    where_clause = (
        f"WHERE {' AND '.join(conditions)}" if conditions else ""
    )

    query = f"""
        SELECT
            f.*,
            COALESCE(p.confidence, '') AS confidence,
            COALESCE(p.is_bookmarked, 0) AS is_bookmarked,
            COALESCE(p.times_viewed, 0) AS times_viewed,
            COALESCE(p.times_correct, 0) AS times_correct,
            COALESCE(p.times_incorrect, 0) AS times_incorrect,
            p.last_reviewed_at,
            p.next_review_at,
            COALESCE(p.review_interval_days, 0) AS review_interval_days,
            COALESCE(p.review_count, 0) AS review_count,
            CASE
                WHEN p.next_review_at IS NULL THEN 1
                WHEN datetime(p.next_review_at) <= datetime('now') THEN 1
                ELSE 0
            END AS is_due
        FROM flashcards f
        LEFT JOIN card_progress p ON p.card_id = f.id
        {where_clause}
        ORDER BY
            CASE WHEN p.next_review_at IS NULL THEN 0 ELSE 1 END,
            p.next_review_at,
            f.exam_part,
            f.topic,
            f.id
    """

    with connect() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def get_due_card_count() -> int:
    initialize_database()

    with connect() as connection:
        return connection.execute(
            """
            SELECT COUNT(*)
            FROM flashcards f
            LEFT JOIN card_progress p ON p.card_id = f.id
            WHERE p.next_review_at IS NULL
               OR datetime(p.next_review_at) <= datetime('now')
            """
        ).fetchone()[0]


def get_weak_card_count() -> int:
    initialize_database()

    with connect() as connection:
        return connection.execute(
            """
            SELECT COUNT(*)
            FROM card_progress
            WHERE confidence IN ('Again', 'Hard')
            """
        ).fetchone()[0]


def record_view(card_id: int) -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO card_progress (card_id, times_viewed)
            VALUES (?, 1)
            ON CONFLICT(card_id) DO UPDATE SET
                times_viewed = times_viewed + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (card_id,),
        )


def set_bookmark(card_id: int, bookmarked: bool) -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO card_progress (card_id, is_bookmarked)
            VALUES (?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                is_bookmarked = excluded.is_bookmarked,
                updated_at = CURRENT_TIMESTAMP
            """,
            (card_id, int(bookmarked)),
        )


def record_result(card_id: int, correct: bool) -> None:
    initialize_database()

    correct_increment = 1 if correct else 0
    incorrect_increment = 0 if correct else 1

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO card_progress (
                card_id,
                times_correct,
                times_incorrect
            )
            VALUES (?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                times_correct = times_correct + excluded.times_correct,
                times_incorrect = times_incorrect + excluded.times_incorrect,
                updated_at = CURRENT_TIMESTAMP
            """,
            (card_id, correct_increment, incorrect_increment),
        )


def _calculate_review_interval(
    confidence: str,
    previous_interval: int,
) -> int:
    """Calculate the next review interval."""

    if confidence == "Again":
        return 0

    if confidence == "Hard":
        return 1

    if confidence == "Good":
        if previous_interval <= 0:
            return 3
        return max(3, round(previous_interval * 1.8))

    if confidence == "Easy":
        if previous_interval <= 0:
            return 7
        return max(7, round(previous_interval * 2.5))

    raise ValueError(f"Unsupported confidence value: {confidence}")


def set_confidence(card_id: int, confidence: str) -> None:
    initialize_database()

    valid_confidence_values = {"Again", "Hard", "Good", "Easy"}

    if confidence not in valid_confidence_values:
        raise ValueError(
            f"Confidence must be one of {sorted(valid_confidence_values)}."
        )

    with connect() as connection:
        progress = connection.execute(
            """
            SELECT review_interval_days
            FROM card_progress
            WHERE card_id = ?
            """,
            (card_id,),
        ).fetchone()

        previous_interval = progress["review_interval_days"] if progress else 0
        next_interval = _calculate_review_interval(
            confidence,
            previous_interval,
        )

        reviewed_at = datetime.now()
        next_review_at = (
            reviewed_at
            if confidence == "Again"
            else reviewed_at + timedelta(days=next_interval)
        )

        connection.execute(
            """
            INSERT INTO card_progress (
                card_id,
                confidence,
                last_reviewed_at,
                next_review_at,
                review_interval_days,
                review_count
            )
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(card_id) DO UPDATE SET
                confidence = excluded.confidence,
                last_reviewed_at = excluded.last_reviewed_at,
                next_review_at = excluded.next_review_at,
                review_interval_days = excluded.review_interval_days,
                review_count = review_count + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                card_id,
                confidence,
                reviewed_at.isoformat(timespec="seconds"),
                next_review_at.isoformat(timespec="seconds"),
                next_interval,
            ),
        )
