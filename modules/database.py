from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "study.db"
CARDS_PATH = ROOT / "data" / "flashcards.json"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
) -> bool:
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(column["name"] == column_name for column in columns)


def _migrate_card_progress(connection: sqlite3.Connection) -> None:
    """Add spaced-repetition columns to an existing database."""

    migrations = {
        "last_reviewed_at": "TEXT",
        "next_review_at": "TEXT",
        "review_interval_days": "INTEGER NOT NULL DEFAULT 0",
        "review_count": "INTEGER NOT NULL DEFAULT 0",
    }

    for column_name, column_definition in migrations.items():
        if not _column_exists(connection, "card_progress", column_name):
            connection.execute(
                f"""
                ALTER TABLE card_progress
                ADD COLUMN {column_name} {column_definition}
                """
            )


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
                last_reviewed_at TEXT,
                next_review_at TEXT,
                review_interval_days INTEGER NOT NULL DEFAULT 0,
                review_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(card_id) REFERENCES flashcards(id)
            );
            """
        )

        _migrate_card_progress(connection)

        count = connection.execute(
            "SELECT COUNT(*) FROM flashcards"
        ).fetchone()[0]

        if count == 0 and CARDS_PATH.exists():
            cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))

            connection.executemany(
                """
                INSERT INTO flashcards (
                    id,
                    exam_part,
                    topic,
                    question,
                    answer,
                    source_file,
                    reference_label,
                    reference_url
                )
                VALUES (
                    :id,
                    :exam_part,
                    :topic,
                    :question,
                    :answer,
                    :source_file,
                    :reference_label,
                    :reference_url
                )
                """,
                cards,
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
                COALESCE(SUM(is_bookmarked), 0),
                COALESCE(SUM(review_count), 0)
            FROM card_progress
            """
        ).fetchone()

        due_cards = connection.execute(
            """
            SELECT COUNT(*)
            FROM flashcards f
            LEFT JOIN card_progress p ON p.card_id = f.id
            WHERE p.next_review_at IS NULL
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
        "reviews": progress[4],
        "due_cards": due_cards,
        "weak_cards": weak_cards,
        "reviewed_today": reviewed_today,
        "by_part": by_part,
    }
