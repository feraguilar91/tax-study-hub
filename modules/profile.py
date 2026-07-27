from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIRECTORY = PROJECT_ROOT / "data"
PROFILE_DATABASE_PATH = DATA_DIRECTORY / "user_profile.db"

DEFAULT_PROFILE = {
    "display_name": "",
    "current_exam_part": "EA Part 1",
    "part_1_exam_date": None,
    "part_2_exam_date": None,
    "part_3_exam_date": None,
    "part_1_passed": False,
    "part_2_passed": False,
    "part_3_passed": False,
    "daily_card_goal": 30,
}


def get_connection() -> sqlite3.Connection:
    """
    Open the profile database and return rows that behave like dictionaries.
    """

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        PROFILE_DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def get_existing_columns(
    connection: sqlite3.Connection,
) -> set[str]:
    """
    Return the column names currently present in the profile table.
    """

    rows = connection.execute(
        """
        PRAGMA table_info(user_profile)
        """
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


def migrate_profile_database(
    connection: sqlite3.Connection,
) -> None:
    """
    Add newer profile fields to an existing database.

    SQLite preserves all existing profile data while the new columns
    are added.
    """

    existing_columns = get_existing_columns(
        connection
    )

    required_columns = {
        "part_1_passed": (
            "INTEGER NOT NULL DEFAULT 0"
        ),
        "part_2_passed": (
            "INTEGER NOT NULL DEFAULT 0"
        ),
        "part_3_passed": (
            "INTEGER NOT NULL DEFAULT 0"
        ),
    }

    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"""
                ALTER TABLE user_profile
                ADD COLUMN {column_name} {column_definition}
                """
            )


def initialize_profile_database() -> None:
    """
    Create and migrate the local profile database.
    """

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                display_name TEXT NOT NULL DEFAULT '',
                current_exam_part TEXT NOT NULL DEFAULT 'EA Part 1',
                part_1_exam_date TEXT,
                part_2_exam_date TEXT,
                part_3_exam_date TEXT,
                part_1_passed INTEGER NOT NULL DEFAULT 0,
                part_2_passed INTEGER NOT NULL DEFAULT 0,
                part_3_passed INTEGER NOT NULL DEFAULT 0,
                daily_card_goal INTEGER NOT NULL DEFAULT 30,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        migrate_profile_database(
            connection
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO user_profile (
                id,
                display_name,
                current_exam_part,
                daily_card_goal
            )
            VALUES (
                1,
                '',
                'EA Part 1',
                30
            )
            """
        )

        connection.commit()


def parse_date(
    value: str | None,
) -> date | None:
    """
    Convert a saved ISO date into a Python date.
    """

    if not value:
        return None

    try:
        return date.fromisoformat(
            value
        )
    except ValueError:
        return None


def serialize_date(
    value: date | None,
) -> str | None:
    """
    Convert a Python date into an ISO date for SQLite.
    """

    if value is None:
        return None

    return value.isoformat()


def get_profile() -> dict[str, Any]:
    """
    Return the saved local user profile.
    """

    initialize_profile_database()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                display_name,
                current_exam_part,
                part_1_exam_date,
                part_2_exam_date,
                part_3_exam_date,
                part_1_passed,
                part_2_passed,
                part_3_passed,
                daily_card_goal
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return DEFAULT_PROFILE.copy()

    return {
        "display_name": (
            row["display_name"]
            or ""
        ),
        "current_exam_part": (
            row["current_exam_part"]
            or "EA Part 1"
        ),
        "part_1_exam_date": parse_date(
            row["part_1_exam_date"]
        ),
        "part_2_exam_date": parse_date(
            row["part_2_exam_date"]
        ),
        "part_3_exam_date": parse_date(
            row["part_3_exam_date"]
        ),
        "part_1_passed": bool(
            row["part_1_passed"]
        ),
        "part_2_passed": bool(
            row["part_2_passed"]
        ),
        "part_3_passed": bool(
            row["part_3_passed"]
        ),
        "daily_card_goal": int(
            row["daily_card_goal"]
            or 30
        ),
    }


def save_profile(
    display_name: str,
    current_exam_part: str,
    part_1_exam_date: date | None,
    part_2_exam_date: date | None,
    part_3_exam_date: date | None,
    daily_card_goal: int,
    part_1_passed: bool = False,
    part_2_passed: bool = False,
    part_3_passed: bool = False,
) -> None:
    """
    Save the local profile, exam dates, and exam completion status.
    """

    initialize_profile_database()

    cleaned_name = display_name.strip()

    valid_exam_parts = {
        "EA Part 1",
        "EA Part 2",
        "EA Part 3",
    }

    if current_exam_part not in valid_exam_parts:
        current_exam_part = "EA Part 1"

    safe_daily_goal = max(
        1,
        int(daily_card_goal),
    )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE user_profile
            SET
                display_name = ?,
                current_exam_part = ?,
                part_1_exam_date = ?,
                part_2_exam_date = ?,
                part_3_exam_date = ?,
                part_1_passed = ?,
                part_2_passed = ?,
                part_3_passed = ?,
                daily_card_goal = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (
                cleaned_name,
                current_exam_part,
                serialize_date(
                    part_1_exam_date
                ),
                serialize_date(
                    part_2_exam_date
                ),
                serialize_date(
                    part_3_exam_date
                ),
                int(
                    bool(part_1_passed)
                ),
                int(
                    bool(part_2_passed)
                ),
                int(
                    bool(part_3_passed)
                ),
                safe_daily_goal,
            ),
        )

        connection.commit()


def get_exam_date(
    profile: dict[str, Any],
    exam_part: str | None = None,
) -> date | None:
    """
    Return the exam date for the selected EA exam part.
    """

    selected_part = (
        exam_part
        or profile.get(
            "current_exam_part",
            "EA Part 1",
        )
    )

    date_key_by_part = {
        "EA Part 1": "part_1_exam_date",
        "EA Part 2": "part_2_exam_date",
        "EA Part 3": "part_3_exam_date",
    }

    date_key = date_key_by_part.get(
        selected_part
    )

    if date_key is None:
        return None

    return profile.get(
        date_key
    )


def has_passed_exam(
    profile: dict[str, Any],
    exam_part: str,
) -> bool:
    """
    Return whether the selected EA exam part has been passed.
    """

    passed_key_by_part = {
        "EA Part 1": "part_1_passed",
        "EA Part 2": "part_2_passed",
        "EA Part 3": "part_3_passed",
    }

    passed_key = passed_key_by_part.get(
        exam_part
    )

    if passed_key is None:
        return False

    return bool(
        profile.get(
            passed_key,
            False,
        )
    )


def get_days_until_exam(
    exam_date: date | None,
) -> int | None:
    """
    Return the number of calendar days until an exam.
    """

    if exam_date is None:
        return None

    return (
        exam_date - date.today()
    ).days


def get_exam_message(
    days_remaining: int | None,
) -> str:
    """
    Return a study recommendation based on time remaining.
    """

    if days_remaining is None:
        return (
            "Add an exam date to receive a personalized countdown "
            "and study recommendation."
        )

    if days_remaining < 0:
        return (
            "This exam date has passed. Mark the exam as passed or "
            "update the date when you schedule another attempt."
        )

    if days_remaining == 0:
        return (
            "Your exam is today. Stay calm, read carefully, and trust "
            "the preparation you have completed."
        )

    if days_remaining <= 7:
        return (
            "Final review week: prioritize weak topics, missed questions, "
            "and concise review sessions."
        )

    if days_remaining <= 14:
        return (
            "Your exam is close. Focus on weak topics and begin or continue "
            "timed practice."
        )

    if days_remaining <= 30:
        return (
            "Increase review consistency and include regular practice "
            "questions in your schedule."
        )

    if days_remaining <= 60:
        return (
            "You have a solid study window. Maintain consistent daily "
            "reviews and reinforce weak areas."
        )

    return (
        "You have time to build a strong foundation. Study consistently "
        "and avoid leaving difficult topics until the end."
    )