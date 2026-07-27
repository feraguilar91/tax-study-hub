from __future__ import annotations

from modules.database import connect, initialize_database


def get_dashboard_stats() -> dict:
    """
    Return aggregate metrics used by the Dashboard and study pages.

    This module owns dashboard reporting queries so the core database
    module can remain focused on connection, initialization, and schema
    management.
    """

    initialize_database()

    with connect() as connection:
        total_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM flashcards
            """
        ).fetchone()[0]

        topics = connection.execute(
            """
            SELECT COUNT(DISTINCT topic)
            FROM flashcards
            """
        ).fetchone()[0]

        parts = connection.execute(
            """
            SELECT COUNT(DISTINCT exam_part)
            FROM flashcards
            """
        ).fetchone()[0]

        progress = connection.execute(
            """
            SELECT
                COALESCE(SUM(times_viewed), 0),
                COALESCE(SUM(times_correct), 0),
                COALESCE(SUM(times_incorrect), 0),
                COALESCE(SUM(is_bookmarked), 0),
                COALESCE(SUM(review_count), 0)
            FROM card_progress
            """
        ).fetchone()

        due_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM flashcards AS f
            LEFT JOIN card_progress AS p
                ON p.card_id = f.id
            WHERE
                p.next_review_at IS NULL
                OR datetime(p.next_review_at) <= datetime('now')
            """
        ).fetchone()[0]

        weak_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM card_progress
            WHERE confidence IN ('Again', 'Hard')
            """
        ).fetchone()[0]

        missed_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM card_progress
            WHERE times_incorrect > 0
            """
        ).fetchone()[0]

        reviewed_today = connection.execute(
            """
            SELECT COUNT(*)
            FROM card_progress
            WHERE date(last_reviewed_at, 'localtime')
                = date('now', 'localtime')
            """
        ).fetchone()[0]

        reviewed_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM card_progress
            WHERE review_count > 0
            """
        ).fetchone()[0]

        mastered_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM card_progress
            WHERE confidence = 'Easy'
            """
        ).fetchone()[0]

        by_part = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    exam_part,
                    COUNT(*) AS card_count
                FROM flashcards
                GROUP BY exam_part
                ORDER BY exam_part
                """
            )
        ]

    return {
        "total_cards": total_cards,
        "topics": topics,
        "parts": parts,
        "views": progress[0],
        "correct": progress[1],
        "incorrect": progress[2],
        "bookmarks": progress[3],
        "reviews": progress[4],
        "total_reviews": progress[4],
        "due_cards": due_cards,
        "weak_cards": weak_cards,
        "missed_cards": missed_cards,
        "reviewed_today": reviewed_today,
        "reviewed_cards": reviewed_cards,
        "mastered_cards": mastered_cards,
        "by_part": by_part,
    }


def get_review_filter_options() -> tuple[list[str], list[str]]:
    """
    Return available exam parts and topics for Progress page filters.
    """

    initialize_database()

    with connect() as connection:
        parts = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT exam_part
                FROM flashcards
                WHERE exam_part IS NOT NULL
                    AND TRIM(exam_part) != ''
                ORDER BY exam_part
                """
            ).fetchall()
        ]

        topics = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT topic
                FROM flashcards
                WHERE topic IS NOT NULL
                    AND TRIM(topic) != ''
                ORDER BY topic
                """
            ).fetchall()
        ]

    return parts, topics


def get_missed_cards() -> list[dict]:
    """
    Return cards answered incorrectly at least once.

    Cards with the highest number of incorrect answers appear first.
    """

    initialize_database()

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                f.id,
                f.exam_part,
                f.topic,
                f.question,
                f.answer,
                f.reference_url,
                p.confidence,
                p.is_bookmarked,
                p.times_viewed,
                p.times_correct,
                p.times_incorrect,
                p.review_count,
                p.updated_at,
                p.last_reviewed_at
            FROM card_progress AS p
            INNER JOIN flashcards AS f
                ON f.id = p.card_id
            WHERE p.times_incorrect > 0
            ORDER BY
                p.times_incorrect DESC,
                p.times_correct ASC,
                datetime(p.updated_at) DESC,
                f.id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_weak_cards() -> list[dict]:
    """
    Return cards currently marked Again or Hard.

    Again cards appear before Hard cards, followed by cards with the
    highest number of incorrect answers.
    """

    initialize_database()

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                f.id,
                f.exam_part,
                f.topic,
                f.question,
                f.answer,
                f.reference_url,
                p.confidence,
                p.is_bookmarked,
                p.times_viewed,
                p.times_correct,
                p.times_incorrect,
                p.review_count,
                p.updated_at,
                p.last_reviewed_at,
                p.next_review_at
            FROM card_progress AS p
            INNER JOIN flashcards AS f
                ON f.id = p.card_id
            WHERE p.confidence IN ('Again', 'Hard')
            ORDER BY
                CASE p.confidence
                    WHEN 'Again' THEN 1
                    WHEN 'Hard' THEN 2
                    ELSE 3
                END,
                p.times_incorrect DESC,
                datetime(p.updated_at) DESC,
                f.id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_bookmarked_cards() -> list[dict]:
    """
    Return cards currently bookmarked by the user.
    """

    initialize_database()

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                f.id,
                f.exam_part,
                f.topic,
                f.question,
                f.answer,
                f.reference_url,
                p.confidence,
                p.is_bookmarked,
                p.times_viewed,
                p.times_correct,
                p.times_incorrect,
                p.review_count,
                p.updated_at,
                p.last_reviewed_at,
                p.next_review_at
            FROM card_progress AS p
            INNER JOIN flashcards AS f
                ON f.id = p.card_id
            WHERE p.is_bookmarked = 1
            ORDER BY
                f.exam_part,
                f.topic,
                datetime(p.updated_at) DESC,
                f.id
            """
        ).fetchall()

    return [dict(row) for row in rows]