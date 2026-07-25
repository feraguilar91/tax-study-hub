from __future__ import annotations

from datetime import datetime

import streamlit as st

from modules.database import (
    get_dashboard_stats,
    get_due_card_count,
    get_weak_card_count,
)
from modules.profile import (
    get_days_until_exam,
    get_exam_date,
    get_exam_message,
    get_profile,
)


st.set_page_config(
    page_title="Dashboard | Tax Study Hub",
    page_icon="📊",
    layout="wide",
)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


def get_greeting() -> str:
    current_hour = datetime.now().hour

    if current_hour < 12:
        return "Good morning"

    if current_hour < 18:
        return "Good afternoon"

    return "Good evening"


def safe_number(
    data: dict,
    *possible_keys: str,
    default: int = 0,
) -> int:
    """
    Return the first available numeric value from a dictionary.
    """

    for key in possible_keys:
        value = data.get(
            key
        )

        if value is not None:
            try:
                return int(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

    return default


def open_flashcards(
    study_mode: str,
) -> None:
    """
    Store the requested study mode and open the Flashcards page.
    """

    st.session_state.dashboard_study_mode = (
        study_mode
    )

    st.session_state.flash_index = 0
    st.session_state.flash_show_answer = False
    st.session_state.flash_shuffle_ids = None

    st.switch_page(
        "pages/1_Flashcards.py"
    )


def format_exam_countdown(
    days_remaining: int | None,
) -> str:
    if days_remaining is None:
        return "Not scheduled"

    if days_remaining < 0:
        return (
            f"{abs(days_remaining)} days ago"
        )

    if days_remaining == 0:
        return "Today"

    if days_remaining == 1:
        return "1 day"

    return f"{days_remaining} days"


# -------------------------------------------------------------------
# Load dashboard information
# -------------------------------------------------------------------

stats = get_dashboard_stats()

due_count = get_due_card_count()
weak_count = get_weak_card_count()

profile = get_profile()

display_name = (
    profile["display_name"].strip()
    or "Student"
)

current_exam_part = profile[
    "current_exam_part"
]

current_exam_date = get_exam_date(
    profile,
    current_exam_part,
)

days_until_exam = get_days_until_exam(
    current_exam_date
)

total_cards = safe_number(
    stats,
    "total_cards",
    "cards",
    "total",
)

bookmarked_cards = safe_number(
    stats,
    "bookmarks",
    "bookmarked_cards",
    "bookmarked",
)

reviewed_cards = safe_number(
    stats,
    "reviewed_cards",
    "cards_reviewed",
    "reviewed",
)

total_reviews = safe_number(
    stats,
    "total_reviews",
    "reviews",
    "review_count",
)

reviewed_today = safe_number(
    stats,
    "reviewed_today",
    "reviews_today",
    "today_reviews",
)

mastered_cards = safe_number(
    stats,
    "mastered_cards",
    "mastered",
    "easy_cards",
)

study_streak = safe_number(
    stats,
    "study_streak",
    "streak",
    "current_streak",
)


# -------------------------------------------------------------------
# Page header
# -------------------------------------------------------------------

st.title("📊 Tax Study Hub")

st.markdown(
    f"## {get_greeting()}, {display_name} 👋"
)

st.caption(
    "See what needs attention and start the right study session."
)

if not profile["display_name"]:
    st.info(
        "Add your name and exam date in Profile & Exam Settings "
        "to personalize your dashboard.",
        icon="⚙️",
    )

st.write("")


# -------------------------------------------------------------------
# Exam countdown
# -------------------------------------------------------------------

with st.container(
    border=True
):
    countdown_column, exam_date_column, settings_column = st.columns(
        [1.2, 1.2, 1]
    )

    with countdown_column:
        st.metric(
            f"📝 {current_exam_part}",
            format_exam_countdown(
                days_until_exam
            ),
            help=(
                "Calendar days remaining before your selected EA exam."
            ),
        )

    with exam_date_column:
        exam_date_text = (
            current_exam_date.strftime(
                "%B %d, %Y"
            )
            if current_exam_date
            else "No exam date"
        )

        st.metric(
            "Exam Date",
            exam_date_text,
        )

    with settings_column:
        st.write("")

        if st.button(
            "⚙️ Profile & Exam Settings",
            use_container_width=True,
        ):
            st.switch_page(
                "pages/3_Profile.py"
            )

    exam_message = get_exam_message(
        days_until_exam
    )

    if days_until_exam is None:
        st.info(
            exam_message,
            icon="📅",
        )
    elif days_until_exam < 0:
        st.warning(
            exam_message,
            icon="⚠️",
        )
    elif days_until_exam <= 14:
        st.warning(
            exam_message,
            icon="⏳",
        )
    else:
        st.success(
            exam_message,
            icon="🎯",
        )


st.write("")


# -------------------------------------------------------------------
# Main statistics
# -------------------------------------------------------------------

metric_column_1, metric_column_2, metric_column_3, metric_column_4 = (
    st.columns(4)
)

with metric_column_1:
    st.metric(
        "📚 Due Today",
        due_count,
        help=(
            "Cards currently scheduled for review."
        ),
    )

with metric_column_2:
    st.metric(
        "💪 Weak Cards",
        weak_count,
        help=(
            "Cards most recently rated Again or Hard."
        ),
    )

with metric_column_3:
    st.metric(
        "⭐ Bookmarked",
        bookmarked_cards,
        help=(
            "Cards saved for focused review."
        ),
    )

with metric_column_4:
    st.metric(
        "🃏 Total Cards",
        total_cards,
        help=(
            "Total flashcards in your study database."
        ),
    )


st.write("")


# -------------------------------------------------------------------
# Today's study section
# -------------------------------------------------------------------

with st.container(
    border=True
):
    st.subheader("Today's Study")

    st.write(
        "Start with cards due for review, then reinforce weak concepts."
    )

    action_column_1, action_column_2, action_column_3 = st.columns(
        3
    )

    with action_column_1:
        if st.button(
            "▶ Start Today's Review",
            type="primary",
            use_container_width=True,
            disabled=(
                due_count == 0
            ),
        ):
            open_flashcards(
                "Due for Review"
            )

        if due_count == 0:
            st.caption(
                "No cards are currently due."
            )
        else:
            st.caption(
                f"{due_count} cards ready for review."
            )

    with action_column_2:
        if st.button(
            "💪 Study Weak Cards",
            use_container_width=True,
            disabled=(
                weak_count == 0
            ),
        ):
            open_flashcards(
                "Weak Cards"
            )

        if weak_count == 0:
            st.caption(
                "No weak cards right now."
            )
        else:
            st.caption(
                f"{weak_count} cards need reinforcement."
            )

    with action_column_3:
        if st.button(
            "📖 Browse All Cards",
            use_container_width=True,
        ):
            open_flashcards(
                "All Cards"
            )

        st.caption(
            "Explore the complete flashcard library."
        )


st.write("")


# -------------------------------------------------------------------
# Progress section
# -------------------------------------------------------------------

with st.container(
    border=True
):
    st.subheader("Study Progress")

    if total_cards > 0:
        reviewed_progress = min(
            reviewed_cards / total_cards,
            1.0,
        )
    else:
        reviewed_progress = 0.0

    progress_percentage = round(
        reviewed_progress * 100
    )

    st.progress(
        reviewed_progress
    )

    st.caption(
        f"{reviewed_cards:,} of {total_cards:,} cards reviewed "
        f"at least once · {progress_percentage}%"
    )

    progress_column_1, progress_column_2, progress_column_3, progress_column_4 = (
        st.columns(4)
    )

    with progress_column_1:
        st.metric(
            "Reviewed Today",
            reviewed_today,
        )

    with progress_column_2:
        st.metric(
            "Total Reviews",
            total_reviews,
        )

    with progress_column_3:
        st.metric(
            "Mastered Cards",
            mastered_cards,
        )

    with progress_column_4:
        st.metric(
            "🔥 Study Streak",
            f"{study_streak} days",
        )


st.write("")


# -------------------------------------------------------------------
# Recommended next action
# -------------------------------------------------------------------

with st.container(
    border=True
):
    st.subheader("Recommended Next Step")

    if due_count > 0:
        st.info(
            f"You have {due_count} cards due. "
            "Start with today's scheduled review.",
            icon="📚",
        )

    elif weak_count > 0:
        st.info(
            "Your scheduled reviews are complete. "
            f"Work through your {weak_count} weak cards next.",
            icon="💪",
        )

    else:
        st.success(
            "You're caught up! Browse all cards or study a topic "
            "you want to strengthen.",
            icon="🎉",
        )