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

            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ended_at TEXT,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                cards_viewed INTEGER NOT NULL DEFAULT 0,
                quiz_answers INTEGER NOT NULL DEFAULT 0,
                reviews INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_study_sessions_started_at
            ON study_sessions(started_at);
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