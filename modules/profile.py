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


def initialize_profile_database() -> None:
    """
    Create the profile table when it does not already exist.

    The first version of the app stores one local profile. Once authentication
    is added, this table can be expanded to store one profile per user.
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
                daily_card_goal INTEGER NOT NULL DEFAULT 30,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
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
                daily_card_goal
            FROM user_profile
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return DEFAULT_PROFILE.copy()

    return {
        "display_name": row["display_name"] or "",
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
        "daily_card_goal": int(
            row["daily_card_goal"] or 30
        ),
    }


def save_profile(
    display_name: str,
    current_exam_part: str,
    part_1_exam_date: date | None,
    part_2_exam_date: date | None,
    part_3_exam_date: date | None,
    daily_card_goal: int,
) -> None:
    """
    Save the local profile and EA exam dates.
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
            "This exam date has passed. Update the date when you "
            "schedule your next exam."
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