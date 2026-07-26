from __future__ import annotations

from modules.database import connect, initialize_database


def get_dashboard_stats() -> dict:
    """
    Return the aggregate metrics used by the Dashboard and study pages.

    This module owns dashboard reporting queries so the core database
    module can remain focused on connection, initialization, and schema
    management.
    """

    initialize_database()

    with connect() as connection:
        total_cards = connection.execute(
            "SELECT COUNT(*) FROM flashcards"
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
            FROM flashcards f
            LEFT JOIN card_progress p
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
        "reviewed_today": reviewed_today,
        "reviewed_cards": reviewed_cards,
        "mastered_cards": mastered_cards,
        "by_part": by_part,
    }
