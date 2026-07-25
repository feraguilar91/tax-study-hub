from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "study.db"
CARDS_PATH = ROOT / "data" / "flashcards.json"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY,
                exam_part TEXT NOT NULL,
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                source_file TEXT,
                reference_label TEXT,
                reference_url TEXT
            );

            CREATE TABLE IF NOT EXISTS card_progress (
                card_id INTEGER PRIMARY KEY,
                confidence TEXT,
                is_bookmarked INTEGER NOT NULL DEFAULT 0,
                times_viewed INTEGER NOT NULL DEFAULT 0,
                times_correct INTEGER NOT NULL DEFAULT 0,
                times_incorrect INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(card_id) REFERENCES flashcards(id)
            );
            """
        )

        count = connection.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0]
        if count == 0 and CARDS_PATH.exists():
            cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
            connection.executemany(
                """
                INSERT INTO flashcards (
                    id, exam_part, topic, question, answer, source_file,
                    reference_label, reference_url
                )
                VALUES (
                    :id, :exam_part, :topic, :question, :answer, :source_file,
                    :reference_label, :reference_url
                )
                """,
                cards,
            )


def get_filter_options() -> tuple[list[str], list[str]]:
    initialize_database()
    with connect() as connection:
        parts = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT exam_part FROM flashcards ORDER BY exam_part"
            )
        ]
        topics = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT topic FROM flashcards ORDER BY topic"
            )
        ]
    return parts, topics


def get_cards(
    exam_part: str | None = None,
    topic: str | None = None,
    search: str | None = None,
    bookmarked_only: bool = False,
) -> list[dict]:
    initialize_database()

    conditions = []
    parameters: list[object] = []

    if exam_part and exam_part != "All":
        conditions.append("f.exam_part = ?")
        parameters.append(exam_part)

    if topic and topic != "All":
        conditions.append("f.topic = ?")
        parameters.append(topic)

    if search:
        conditions.append(
            "(f.question LIKE ? OR f.answer LIKE ? OR f.topic LIKE ?)"
        )
        pattern = f"%{search}%"
        parameters.extend([pattern, pattern, pattern])

    if bookmarked_only:
        conditions.append("COALESCE(p.is_bookmarked, 0) = 1")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            f.*,
            COALESCE(p.confidence, '') AS confidence,
            COALESCE(p.is_bookmarked, 0) AS is_bookmarked,
            COALESCE(p.times_viewed, 0) AS times_viewed,
            COALESCE(p.times_correct, 0) AS times_correct,
            COALESCE(p.times_incorrect, 0) AS times_incorrect
        FROM flashcards f
        LEFT JOIN card_progress p ON p.card_id = f.id
        {where_clause}
        ORDER BY f.exam_part, f.topic, f.id
    """

    with connect() as connection:
        return [dict(row) for row in connection.execute(query, parameters)]


def record_view(card_id: int) -> None:
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
    correct_increment = 1 if correct else 0
    incorrect_increment = 0 if correct else 1

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO card_progress (
                card_id, times_correct, times_incorrect
            )
            VALUES (?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                times_correct = times_correct + excluded.times_correct,
                times_incorrect = times_incorrect + excluded.times_incorrect,
                updated_at = CURRENT_TIMESTAMP
            """,
            (card_id, correct_increment, incorrect_increment),
        )


def set_confidence(card_id: int, confidence: str) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO card_progress (card_id, confidence)
            VALUES (?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                confidence = excluded.confidence,
                updated_at = CURRENT_TIMESTAMP
            """,
            (card_id, confidence),
        )


def get_dashboard_stats() -> dict:
    initialize_database()
    with connect() as connection:
        total_cards = connection.execute(
            "SELECT COUNT(*) FROM flashcards"
        ).fetchone()[0]
        topics = connection.execute(
            "SELECT COUNT(DISTINCT topic) FROM flashcards"
        ).fetchone()[0]
        parts = connection.execute(
            "SELECT COUNT(DISTINCT exam_part) FROM flashcards"
        ).fetchone()[0]
        progress = connection.execute(
            """
            SELECT
                COALESCE(SUM(times_viewed), 0),
                COALESCE(SUM(times_correct), 0),
                COALESCE(SUM(times_incorrect), 0),
                COALESCE(SUM(is_bookmarked), 0)
            FROM card_progress
            """
        ).fetchone()

        by_part = [
            dict(row)
            for row in connection.execute(
                """
                SELECT exam_part, COUNT(*) AS card_count
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
        "by_part": by_part,
    }
