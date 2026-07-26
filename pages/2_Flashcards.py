from __future__ import annotations

import random

import streamlit as st

from modules.dashboard import get_dashboard_stats
from modules.flashcards import (
    get_cards,
    get_due_card_count,
    get_filter_options,
    get_weak_card_count,
    set_bookmark,
)

from modules.progress_engine import (
    record_review,
    record_view,
)

from modules.ui import reference_link, reset_navigation


st.set_page_config(
    page_title="Flashcards | Tax Study Hub",
    page_icon="🃏",
    layout="centered",
)

st.title("🃏 Flashcards")
st.caption(
    "Review tax concepts, rate your confidence, "
    "and focus on the cards that need the most attention."
)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


def move_to_previous_card() -> None:
    if st.session_state.flash_index > 0:
        st.session_state.flash_index -= 1

    st.session_state.flash_show_answer = False


def move_to_next_card(card_count: int) -> None:
    if st.session_state.flash_index < card_count - 1:
        st.session_state.flash_index += 1

    st.session_state.flash_show_answer = False


def reset_flashcard_session() -> None:
    st.session_state.flash_index = 0
    st.session_state.flash_show_answer = False
    st.session_state.flash_shuffle_ids = None


def apply_shuffled_order(cards: list[dict]) -> list[dict]:
    shuffled_ids = st.session_state.get("flash_shuffle_ids")

    if not shuffled_ids:
        return cards

    cards_by_id = {
        card["id"]: card
        for card in cards
    }

    ordered_cards = [
        cards_by_id[card_id]
        for card_id in shuffled_ids
        if card_id in cards_by_id
    ]

    ordered_card_ids = {
        card["id"]
        for card in ordered_cards
    }

    ordered_cards.extend(
        card
        for card in cards
        if card["id"] not in ordered_card_ids
    )

    return ordered_cards


# -------------------------------------------------------------------
# Data and sidebar
# -------------------------------------------------------------------

parts, topics = get_filter_options()

stats = get_dashboard_stats()
due_count = get_due_card_count()
weak_count = get_weak_card_count()

with st.sidebar:
    st.header("Study overview")

    metric_column_1, metric_column_2 = st.columns(2)

    with metric_column_1:
        st.metric(
            "Due",
            due_count,
            help="Cards that are ready for review.",
        )

    with metric_column_2:
        st.metric(
            "Weak",
            weak_count,
            help="Cards rated Again or Hard.",
        )

    st.metric(
        "Bookmarked",
        stats["bookmarks"],
        help="Cards you have saved for later review.",
    )

    st.divider()

    st.header("Study mode")

    study_mode = st.radio(
        "Choose which cards to study",
        [
            "All Cards",
            "Due for Review",
            "Weak Cards",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.header("Filters")

    selected_part = st.selectbox(
        "EA exam part",
        ["All"] + parts,
    )

    selected_topic = st.selectbox(
        "Topic",
        ["All"] + topics,
    )

    bookmarked_only = st.checkbox(
        "Bookmarked only",
    )

    search = st.text_input(
        "Search cards",
        placeholder="Search questions or answers",
    )

    st.divider()

    if st.button(
        "Reset study session",
        use_container_width=True,
    ):
        reset_flashcard_session()
        st.rerun()


# -------------------------------------------------------------------
# Filter handling
# -------------------------------------------------------------------

filter_signature = (
    study_mode,
    selected_part,
    selected_topic,
    bookmarked_only,
    search.strip().lower(),
)

if st.session_state.get("flash_filter_signature") != filter_signature:
    st.session_state.flash_filter_signature = filter_signature
    st.session_state.flash_shuffle_ids = None
    reset_navigation("flash")


cards = get_cards(
    exam_part=selected_part,
    topic=selected_topic,
    search=search.strip() or None,
    bookmarked_only=bookmarked_only,
    due_only=(study_mode == "Due for Review"),
    weak_only=(study_mode == "Weak Cards"),
)


if not cards:
    if study_mode == "Due for Review":
        st.success(
            "You have no cards due for review right now. Great work! 🎉"
        )
    elif study_mode == "Weak Cards":
        st.success(
            "You currently have no cards rated Again or Hard. Nice job! 🎉"
        )
    else:
        st.warning(
            "No flashcards match the selected filters."
        )

    st.stop()


# -------------------------------------------------------------------
# Session state
# -------------------------------------------------------------------

st.session_state.setdefault(
    "flash_index",
    0,
)

st.session_state.setdefault(
    "flash_show_answer",
    False,
)

st.session_state.setdefault(
    "flash_shuffle_ids",
    None,
)


# -------------------------------------------------------------------
# Shuffle controls
# -------------------------------------------------------------------

shuffle_column, reset_column, mode_column = st.columns(
    [1, 1, 1.4]
)

with shuffle_column:
    if st.button(
        "🔀 Shuffle",
        use_container_width=True,
        help="Shuffle the current card set.",
    ):
        shuffled_ids = [
            card["id"]
            for card in cards
        ]

        random.shuffle(shuffled_ids)

        st.session_state.flash_shuffle_ids = shuffled_ids
        st.session_state.flash_index = 0
        st.session_state.flash_show_answer = False

        st.rerun()


with reset_column:
    if st.button(
        "↩ Reset order",
        use_container_width=True,
        help="Restore the original card order.",
    ):
        st.session_state.flash_shuffle_ids = None
        st.session_state.flash_index = 0
        st.session_state.flash_show_answer = False

        st.rerun()


with mode_column:
    if st.session_state.flash_shuffle_ids:
        st.info(
            "Shuffle active",
            icon="🔀",
        )
    else:
        st.info(
            study_mode,
            icon="📚",
        )


cards = apply_shuffled_order(cards)


# -------------------------------------------------------------------
# Current card
# -------------------------------------------------------------------

st.session_state.flash_index = min(
    st.session_state.flash_index,
    len(cards) - 1,
)

st.session_state.flash_index = max(
    st.session_state.flash_index,
    0,
)

card = cards[
    st.session_state.flash_index
]


# -------------------------------------------------------------------
# Record card view
# -------------------------------------------------------------------

view_key = (
    f'flash_viewed_{card["id"]}'
)

if not st.session_state.get(view_key):
    record_view(
        card["id"]
    )

    st.session_state[view_key] = True


# -------------------------------------------------------------------
# Progress information
# -------------------------------------------------------------------

current_card_number = (
    st.session_state.flash_index + 1
)

progress_value = (
    current_card_number / len(cards)
)

st.progress(
    progress_value
)

st.caption(
    f"Card {current_card_number} of {len(cards)}"
    f' · {card["exam_part"]}'
    f' · {card["topic"]}'
)


# -------------------------------------------------------------------
# Flashcard display
# -------------------------------------------------------------------

with st.container(
    border=True,
):
    heading_column, bookmark_column = st.columns(
        [5, 1]
    )

    with heading_column:
        st.markdown(
            "### Question"
        )

    with bookmark_column:
        bookmark_icon = (
            "★"
            if card["is_bookmarked"]
            else "☆"
        )

        bookmark_help = (
            "Remove bookmark"
            if card["is_bookmarked"]
            else "Bookmark this card"
        )

        if st.button(
            bookmark_icon,
            key=f'bookmark_{card["id"]}',
            use_container_width=True,
            help=bookmark_help,
        ):
            set_bookmark(
                card["id"],
                not bool(
                    card["is_bookmarked"]
                ),
            )

            st.rerun()

    st.markdown(
        f"""
        <div style="
            padding: 1.25rem;
            border-radius: 0.75rem;
            background-color: rgba(128, 128, 128, 0.10);
            font-size: 1.1rem;
            line-height: 1.65;
        ">
            {card["question"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    answer_button_label = (
        "Hide answer"
        if st.session_state.flash_show_answer
        else "Show answer"
    )

    if st.button(
        answer_button_label,
        type="primary",
        use_container_width=True,
        key=f'show_answer_{card["id"]}',
    ):
        st.session_state.flash_show_answer = (
            not st.session_state.flash_show_answer
        )

        st.rerun()

    if st.session_state.flash_show_answer:
        st.divider()

        st.markdown(
            "### Answer"
        )

        st.markdown(
            f"""
            <div style="
                padding: 1.25rem;
                border-radius: 0.75rem;
                background-color: rgba(46, 160, 67, 0.12);
                font-size: 1.05rem;
                line-height: 1.65;
            ">
                {card["answer"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        reference_link(
            card
        )

        next_review_text = {
            "Again": "Review again now",
            "Hard": "Review tomorrow",
            "Good": "Review in about 3 days",
            "Easy": "Review in about 7 days",
        }

        st.markdown(
            "#### How well did you know it?"
        )

        confidence_columns = st.columns(
            4
        )

        confidence_options = [
            ("Again", "Review again now"),
            ("Hard", "Review tomorrow"),
            ("Good", "Review in a few days"),
            ("Easy", "Review next week"),
        ]

        for column, (
            label,
            help_text,
        ) in zip(
            confidence_columns,
            confidence_options,
        ):
            with column:
                if st.button(
                    label,
                    use_container_width=True,
                    key=(
                        f'confidence_{label}_'
                        f'{card["id"]}'
                    ),
                    help=help_text,
                ):
                    record_review(
                        card["id"],
                        label,
                    )

                    st.toast(
                        next_review_text[label]
                    )

                    move_to_next_card(
                        len(cards)
                    )

                    st.rerun()


# -------------------------------------------------------------------
# Navigation
# -------------------------------------------------------------------

st.write("")

previous_column, position_column, next_column = st.columns(
    [1, 1.4, 1]
)

with previous_column:
    previous_disabled = (
        st.session_state.flash_index == 0
    )

    if st.button(
        "← Previous",
        use_container_width=True,
        disabled=previous_disabled,
    ):
        move_to_previous_card()
        st.rerun()


with position_column:
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding-top: 0.55rem;
            font-weight: 600;
        ">
            {current_card_number} / {len(cards)}
        </div>
        """,
        unsafe_allow_html=True,
    )


with next_column:
    next_disabled = (
        st.session_state.flash_index
        >= len(cards) - 1
    )

    if st.button(
        "Next →",
        use_container_width=True,
        disabled=next_disabled,
    ):
        move_to_next_card(
            len(cards)
        )

        st.rerun()


if st.session_state.flash_index == len(cards) - 1:
    st.success(
        "You reached the end of this flashcard set! 🎉"
    )