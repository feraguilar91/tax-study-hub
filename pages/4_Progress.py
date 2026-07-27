from __future__ import annotations

import streamlit as st

from modules.dashboard import (
    get_bookmarked_cards,
    get_dashboard_stats,
    get_missed_cards,
    get_review_filter_options,
    get_weak_cards,
)
from modules.ui import reference_link


st.set_page_config(
    page_title="Progress | Tax Study Hub",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Progress")
st.caption(
    "Track your performance and review the questions that need more work."
)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


def filter_cards(
    cards: list[dict],
    exam_part: str,
    topic: str,
) -> list[dict]:
    """
    Filter a card list by the selected exam part and topic.
    """

    filtered_cards = cards

    if exam_part != "All":
        filtered_cards = [
            card
            for card in filtered_cards
            if card["exam_part"] == exam_part
        ]

    if topic != "All":
        filtered_cards = [
            card
            for card in filtered_cards
            if card["topic"] == topic
        ]

    return filtered_cards


def start_focused_review(
    cards: list[dict],
    label: str,
) -> None:
    """
    Store a temporary review deck and open the Flashcards page.
    """

    st.session_state.focused_review_ids = [
        card["id"]
        for card in cards
    ]

    st.session_state.focused_review_label = label
    st.session_state.flash_index = 0
    st.session_state.flash_show_answer = False
    st.session_state.flash_shuffle_ids = None
    st.session_state.pop(
        "flash_filter_signature",
        None,
    )

    st.switch_page(
        "pages/2_Flashcards.py"
    )


def build_review_label(
    category: str,
    exam_part: str,
    topic: str,
) -> str:
    """
    Build the title displayed on the focused Flashcards deck.
    """

    label_parts = [
        category
    ]

    if exam_part != "All":
        label_parts.append(
            exam_part
        )

    if topic != "All":
        label_parts.append(
            topic
        )

    return " · ".join(
        label_parts
    )


def display_review_button(
    cards: list[dict],
    label: str,
    key: str,
) -> None:
    """
    Display a button that launches the supplied cards in Flashcards.
    """

    card_count = len(cards)

    button_label = (
        f"▶ Review This Card"
        if card_count == 1
        else f"▶ Review These {card_count} Cards"
    )

    if st.button(
        button_label,
        type="primary",
        use_container_width=True,
        disabled=(
            card_count == 0
        ),
        key=key,
    ):
        start_focused_review(
            cards,
            label,
        )


def display_card_details(
    card: dict,
    *,
    show_review_count: bool = False,
) -> None:
    """
    Display the answer, reference, and performance details for one card.
    """

    confidence = (
        card.get("confidence")
        or "Not rated"
    )

    detail_col1, detail_col2, detail_col3 = st.columns(
        3
    )

    detail_col1.markdown(
        f'**Exam part:** {card["exam_part"]}'
    )

    detail_col2.markdown(
        f'**Topic:** {card["topic"]}'
    )

    detail_col3.markdown(
        f"**Confidence:** {confidence}"
    )

    st.markdown(
        "#### Correct answer"
    )

    st.success(
        card["answer"]
    )

    reference_link(
        card
    )

    result_col1, result_col2, result_col3 = st.columns(
        3
    )

    result_col1.metric(
        "Correct",
        card["times_correct"],
    )

    result_col2.metric(
        "Missed",
        card["times_incorrect"],
    )

    if show_review_count:
        result_col3.metric(
            "Reviews",
            card["review_count"],
        )

    else:
        result_col3.metric(
            "Times viewed",
            card["times_viewed"],
        )


# -------------------------------------------------------------------
# Dashboard statistics
# -------------------------------------------------------------------

stats = get_dashboard_stats()

col1, col2, col3, col4 = st.columns(
    4
)

col1.metric(
    "Cards viewed",
    stats["views"],
)

col2.metric(
    "Correct answers",
    stats["correct"],
)

col3.metric(
    "Missed answers",
    stats["incorrect"],
)

col4.metric(
    "Bookmarks",
    stats["bookmarks"],
)


attempts = (
    stats["correct"]
    + stats["incorrect"]
)

accuracy = (
    stats["correct"] / attempts * 100
    if attempts
    else 0
)


st.markdown(
    "### Quiz accuracy"
)

accuracy_col, attempts_col, review_col = st.columns(
    3
)

accuracy_col.metric(
    "Accuracy",
    f"{accuracy:.1f}%",
)

attempts_col.metric(
    "Total quiz answers",
    attempts,
)

review_col.metric(
    "Confidence reviews",
    stats["reviews"],
)

st.progress(
    min(
        accuracy / 100,
        1.0,
    )
)


# -------------------------------------------------------------------
# Review center
# -------------------------------------------------------------------

st.divider()

st.markdown(
    "## Review center"
)

st.caption(
    "Filter your study history by exam part and topic, then launch "
    "a focused flashcard session containing only those cards."
)

available_parts, available_topics = get_review_filter_options()

all_missed_cards = get_missed_cards()
all_weak_cards = get_weak_cards()
all_bookmarked_cards = get_bookmarked_cards()

all_review_cards = (
    all_missed_cards
    + all_weak_cards
    + all_bookmarked_cards
)

filter_col1, filter_col2 = st.columns(
    2
)

with filter_col1:
    selected_part = st.selectbox(
        "Exam part",
        ["All"] + available_parts,
        key="progress_exam_part_filter",
    )


if selected_part == "All":
    topics_for_selected_part = available_topics

else:
    topics_for_selected_part = sorted(
        {
            card["topic"]
            for card in all_review_cards
            if card["exam_part"] == selected_part
        }
    )


current_topic = st.session_state.get(
    "progress_topic_filter",
    "All",
)

valid_topic_options = (
    ["All"]
    + topics_for_selected_part
)

if current_topic not in valid_topic_options:
    st.session_state.progress_topic_filter = "All"


with filter_col2:
    selected_topic = st.selectbox(
        "Topic",
        valid_topic_options,
        key="progress_topic_filter",
    )


missed_cards = filter_cards(
    all_missed_cards,
    selected_part,
    selected_topic,
)

weak_cards = filter_cards(
    all_weak_cards,
    selected_part,
    selected_topic,
)

bookmarked_cards = filter_cards(
    all_bookmarked_cards,
    selected_part,
    selected_topic,
)


active_filters = []

if selected_part != "All":
    active_filters.append(
        selected_part
    )

if selected_topic != "All":
    active_filters.append(
        selected_topic
    )

if active_filters:
    st.info(
        "Showing review cards for: "
        + " → ".join(active_filters)
    )


missed_label = build_review_label(
    "Missed Questions",
    selected_part,
    selected_topic,
)

weak_label = build_review_label(
    "Again / Hard Cards",
    selected_part,
    selected_topic,
)

bookmarked_label = build_review_label(
    "Bookmarked Cards",
    selected_part,
    selected_topic,
)


missed_tab, weak_tab, bookmarked_tab = st.tabs(
    [
        f"Missed questions ({len(missed_cards)})",
        f"Again / Hard ({len(weak_cards)})",
        f"Bookmarked ({len(bookmarked_cards)})",
    ]
)


# -------------------------------------------------------------------
# Missed quiz questions
# -------------------------------------------------------------------

with missed_tab:
    st.markdown(
        "### Questions missed in quizzes"
    )

    st.caption(
        "These cards have been answered incorrectly at least once. "
        "Cards with the most missed answers appear first."
    )

    display_review_button(
        missed_cards,
        missed_label,
        "review_missed_cards",
    )

    st.write("")

    if not missed_cards:
        st.success(
            "No missed questions match the selected filters."
        )

    for position, card in enumerate(
        missed_cards,
        start=1,
    ):
        missed_word = (
            "time"
            if card["times_incorrect"] == 1
            else "times"
        )

        expander_title = (
            f'{position}. {card["question"]} '
            f'— missed {card["times_incorrect"]} {missed_word}'
        )

        with st.expander(
            expander_title
        ):
            display_card_details(
                card
            )


# -------------------------------------------------------------------
# Weak flashcards
# -------------------------------------------------------------------

with weak_tab:
    st.markdown(
        "### Cards marked Again or Hard"
    )

    st.caption(
        "These cards were marked as difficult during flashcard review."
    )

    display_review_button(
        weak_cards,
        weak_label,
        "review_weak_cards",
    )

    st.write("")

    if not weak_cards:
        st.success(
            "No Again or Hard cards match the selected filters."
        )

    for position, card in enumerate(
        weak_cards,
        start=1,
    ):
        confidence = (
            card.get("confidence")
            or "Not rated"
        )

        expander_title = (
            f'{position}. [{confidence}] '
            f'{card["question"]}'
        )

        with st.expander(
            expander_title
        ):
            display_card_details(
                card,
                show_review_count=True,
            )


# -------------------------------------------------------------------
# Bookmarked cards
# -------------------------------------------------------------------

with bookmarked_tab:
    st.markdown(
        "### Bookmarked cards"
    )

    st.caption(
        "These are cards you saved for later review."
    )

    display_review_button(
        bookmarked_cards,
        bookmarked_label,
        "review_bookmarked_cards",
    )

    st.write("")

    if not bookmarked_cards:
        st.success(
            "No bookmarked cards match the selected filters."
        )

    for position, card in enumerate(
        bookmarked_cards,
        start=1,
    ):
        confidence = (
            card.get("confidence")
            or "Not rated"
        )

        expander_title = (
            f'{position}. ⭐ {card["question"]} '
            f'— {confidence}'
        )

        with st.expander(
            expander_title
        ):
            display_card_details(
                card,
                show_review_count=True,
            )


# -------------------------------------------------------------------
# Library size
# -------------------------------------------------------------------

st.divider()

st.markdown(
    "## Library size"
)

for row in stats["by_part"]:
    st.write(
        f'**{row["exam_part"]}:** '
        f'{row["card_count"]} cards'
    )