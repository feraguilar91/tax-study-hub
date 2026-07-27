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
    """
    Move backward one card while preserving the locked deck order.
    """

    if st.session_state.flash_index > 0:
        st.session_state.flash_index -= 1

    st.session_state.flash_show_answer = False


def move_to_next_card(card_count: int) -> None:
    """
    Move forward one card while preserving the locked deck order.
    """

    if st.session_state.flash_index < card_count - 1:
        st.session_state.flash_index += 1

    st.session_state.flash_show_answer = False


def clear_flashcard_deck() -> None:
    """
    Clear all state associated with the current flashcard deck.
    """

    st.session_state.flash_index = 0
    st.session_state.flash_show_answer = False
    st.session_state.flash_shuffle_ids = None
    st.session_state.flash_deck_ids = None


def reset_flashcard_session() -> None:
    """
    Restart the current deck from its first card.

    The locked deck itself is preserved.
    """

    st.session_state.flash_index = 0
    st.session_state.flash_show_answer = False
    st.session_state.flash_shuffle_ids = None


def order_cards_by_ids(
    cards: list[dict],
    card_ids: list[int],
) -> list[dict]:
    """
    Return cards in the exact order specified by card_ids.
    """

    cards_by_id = {
        card["id"]: card
        for card in cards
    }

    return [
        cards_by_id[card_id]
        for card_id in card_ids
        if card_id in cards_by_id
    ]


def get_locked_deck_cards() -> list[dict]:
    """
    Load current card data while preserving the locked deck order.

    Card statistics, bookmarks, and confidence may change during a
    session. The card order must not change when those updates occur.
    """

    deck_ids = st.session_state.get(
        "flash_deck_ids"
    ) or []

    if not deck_ids:
        return []

    all_cards = get_cards()

    ordered_cards = order_cards_by_ids(
        all_cards,
        deck_ids,
    )

    shuffle_ids = st.session_state.get(
        "flash_shuffle_ids"
    )

    if shuffle_ids:
        ordered_cards = order_cards_by_ids(
            ordered_cards,
            shuffle_ids,
        )

    return ordered_cards


def lock_deck(
    cards: list[dict],
) -> None:
    """
    Save the current card order for the duration of the study session.
    """

    st.session_state.flash_deck_ids = [
        card["id"]
        for card in cards
    ]

    st.session_state.flash_shuffle_ids = None
    st.session_state.flash_index = 0
    st.session_state.flash_show_answer = False


def exit_focused_review() -> None:
    """
    Clear the temporary focused-review deck.
    """

    st.session_state.pop(
        "focused_review_ids",
        None,
    )

    st.session_state.pop(
        "focused_review_label",
        None,
    )

    clear_flashcard_deck()
    reset_navigation("flash")


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

st.session_state.setdefault(
    "flash_deck_ids",
    None,
)

study_session_id = st.session_state.get(
    "study_session_id"
)

focused_review_ids = st.session_state.get(
    "focused_review_ids",
    [],
)

focused_review_label = st.session_state.get(
    "focused_review_label",
    "Focused Review",
)

focused_review_active = bool(
    focused_review_ids
)


# -------------------------------------------------------------------
# Data
# -------------------------------------------------------------------

parts, topics = get_filter_options()

stats = get_dashboard_stats()
due_count = get_due_card_count()
weak_count = get_weak_card_count()


# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

with st.sidebar:
    st.header("Study overview")

    metric_column_1, metric_column_2 = st.columns(
        2
    )

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

    if focused_review_active:
        st.header("Focused review")

        st.info(
            focused_review_label,
            icon="🎯",
        )

        st.metric(
            "Cards in deck",
            len(focused_review_ids),
        )

        if st.button(
            "Exit focused review",
            use_container_width=True,
        ):
            exit_focused_review()
            st.rerun()

        st.divider()

        if st.button(
            "Restart focused review",
            use_container_width=True,
        ):
            reset_flashcard_session()
            st.rerun()

    else:
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
            clear_flashcard_deck()
            st.rerun()


# -------------------------------------------------------------------
# Determine the selected deck
# -------------------------------------------------------------------

if focused_review_active:
    filter_signature = (
        "focused_review",
        tuple(focused_review_ids),
        focused_review_label,
    )

    display_mode = focused_review_label

else:
    filter_signature = (
        "normal",
        study_mode,
        selected_part,
        selected_topic,
        bookmarked_only,
        search.strip().lower(),
    )

    display_mode = study_mode


# -------------------------------------------------------------------
# Lock a new deck when the source or filters change
# -------------------------------------------------------------------

previous_signature = st.session_state.get(
    "flash_filter_signature"
)

if previous_signature != filter_signature:
    st.session_state.flash_filter_signature = filter_signature
    st.session_state.flash_deck_ids = None
    st.session_state.flash_shuffle_ids = None
    reset_navigation("flash")


if not st.session_state.get("flash_deck_ids"):
    if focused_review_active:
        all_cards = get_cards()

        initial_cards = order_cards_by_ids(
            all_cards,
            focused_review_ids,
        )

    else:
        initial_cards = get_cards(
            exam_part=selected_part,
            topic=selected_topic,
            search=search.strip() or None,
            bookmarked_only=bookmarked_only,
            due_only=(
                study_mode == "Due for Review"
            ),
            weak_only=(
                study_mode == "Weak Cards"
            ),
        )

    if initial_cards:
        lock_deck(
            initial_cards
        )


cards = get_locked_deck_cards()


# -------------------------------------------------------------------
# Empty deck handling
# -------------------------------------------------------------------

if not cards:
    if focused_review_active:
        st.warning(
            "The focused-review deck no longer contains any available cards."
        )

        if st.button(
            "Exit focused review",
            type="primary",
            use_container_width=True,
        ):
            exit_focused_review()
            st.rerun()

    elif study_mode == "Due for Review":
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
# Focused-review heading
# -------------------------------------------------------------------

if focused_review_active:
    heading_column, exit_column = st.columns(
        [3, 1]
    )

    with heading_column:
        st.info(
            f"Focused review: {focused_review_label}",
            icon="🎯",
        )

    with exit_column:
        if st.button(
            "Exit review",
            use_container_width=True,
        ):
            exit_focused_review()
            st.rerun()


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
        help="Shuffle the current locked card set.",
    ):
        shuffled_ids = list(
            st.session_state.flash_deck_ids
        )

        random.shuffle(
            shuffled_ids
        )

        st.session_state.flash_shuffle_ids = shuffled_ids
        st.session_state.flash_index = 0
        st.session_state.flash_show_answer = False

        st.rerun()


with reset_column:
    if st.button(
        "↩ Reset order",
        use_container_width=True,
        help="Restore the deck's original locked order.",
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

    elif focused_review_active:
        st.info(
            "Focused review",
            icon="🎯",
        )

    else:
        st.info(
            display_mode,
            icon="📚",
        )


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
        card["id"],
        session_id=study_session_id,
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
                        session_id=study_session_id,
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

previous_column, counter_column, next_column = st.columns(
    [1, 1.5, 1]
)

with previous_column:
    if st.button(
        "← Previous",
        use_container_width=True,
        disabled=(
            st.session_state.flash_index == 0
        ),
    ):
        move_to_previous_card()
        st.rerun()


with counter_column:
    st.markdown(
        (
            "<div style='text-align: center; padding-top: 0.5rem;'>"
            f"{current_card_number} / {len(cards)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


with next_column:
    if st.button(
        "Next →",
        use_container_width=True,
        disabled=(
            st.session_state.flash_index
            >= len(cards) - 1
        ),
    ):
        move_to_next_card(
            len(cards)
        )

        st.rerun()


# -------------------------------------------------------------------
# Focused-review completion
# -------------------------------------------------------------------

if (
    focused_review_active
    and current_card_number == len(cards)
):
    st.divider()

    st.success(
        "You reached the final card in this focused-review deck.",
        icon="🎉",
    )

    completion_column, restart_column = st.columns(
        2
    )

    with completion_column:
        if st.button(
            "Finish focused review",
            type="primary",
            use_container_width=True,
        ):
            exit_focused_review()

            st.switch_page(
                "pages/4_Progress.py"
            )

    with restart_column:
        if st.button(
            "Review deck again",
            use_container_width=True,
        ):
            reset_flashcard_session()
            st.rerun()