import random

import streamlit as st

from modules.database import (
    get_cards,
    get_filter_options,
    record_view,
    set_bookmark,
    set_confidence,
)
from modules.ui import reference_link, reset_navigation


st.set_page_config(
    page_title="Flashcards | Tax Study Hub",
    page_icon="🃏",
    layout="centered",
)

st.title("🃏 Flashcards")
st.caption("Review tax concepts, rate your confidence, and track your progress.")


# -------------------------------------------------------------------
# Filters
# -------------------------------------------------------------------

parts, topics = get_filter_options()

with st.sidebar:
    st.header("Study filters")

    selected_part = st.selectbox(
        "EA exam part",
        ["All"] + parts,
    )

    selected_topic = st.selectbox(
        "Topic",
        ["All"] + topics,
    )

    bookmarked_only = st.checkbox("Bookmarked only")

    search = st.text_input(
        "Search cards",
        placeholder="Search questions or answers",
    )


filter_signature = (
    selected_part,
    selected_topic,
    bookmarked_only,
    search.strip().lower(),
)


# Reset card position and shuffle whenever filters change.
if st.session_state.get("flash_filter_signature") != filter_signature:
    st.session_state.flash_filter_signature = filter_signature
    st.session_state.flash_shuffle_ids = None
    reset_navigation("flash")


cards = get_cards(
    exam_part=selected_part,
    topic=selected_topic,
    search=search.strip() or None,
    bookmarked_only=bookmarked_only,
)


if not cards:
    st.warning("No flashcards match the selected filters.")
    st.stop()


# -------------------------------------------------------------------
# Session state
# -------------------------------------------------------------------

st.session_state.setdefault("flash_index", 0)
st.session_state.setdefault("flash_show_answer", False)
st.session_state.setdefault("flash_shuffle_ids", None)


# -------------------------------------------------------------------
# Shuffle controls
# -------------------------------------------------------------------

control_col1, control_col2, control_col3 = st.columns([1, 1, 2])

with control_col1:
    if st.button(
        "🔀 Shuffle",
        use_container_width=True,
        help="Shuffle the current set of cards.",
    ):
        shuffled_ids = [card["id"] for card in cards]
        random.shuffle(shuffled_ids)

        st.session_state.flash_shuffle_ids = shuffled_ids
        st.session_state.flash_index = 0
        st.session_state.flash_show_answer = False
        st.rerun()


with control_col2:
    if st.button(
        "↩ Reset order",
        use_container_width=True,
        help="Return cards to their original order.",
    ):
        st.session_state.flash_shuffle_ids = None
        st.session_state.flash_index = 0
        st.session_state.flash_show_answer = False
        st.rerun()


with control_col3:
    if st.session_state.flash_shuffle_ids:
        st.info("Shuffle mode is active.", icon="🔀")


# Apply the saved shuffled order.
if st.session_state.flash_shuffle_ids:
    cards_by_id = {card["id"]: card for card in cards}

    ordered_cards = [
        cards_by_id[card_id]
        for card_id in st.session_state.flash_shuffle_ids
        if card_id in cards_by_id
    ]

    # Include any new cards that were not present when shuffle began.
    shuffled_id_set = set(st.session_state.flash_shuffle_ids)
    ordered_cards.extend(
        card
        for card in cards
        if card["id"] not in shuffled_id_set
    )

    cards = ordered_cards


# Keep the index inside the valid range.
st.session_state.flash_index = min(
    st.session_state.flash_index,
    len(cards) - 1,
)


card = cards[st.session_state.flash_index]


# -------------------------------------------------------------------
# Record card view
# -------------------------------------------------------------------

view_key = f'flash_viewed_{card["id"]}'

if not st.session_state.get(view_key):
    record_view(card["id"])
    st.session_state[view_key] = True


# -------------------------------------------------------------------
# Progress
# -------------------------------------------------------------------

current_card_number = st.session_state.flash_index + 1
progress = current_card_number / len(cards)

st.progress(progress)

st.caption(
    f'Card {current_card_number} of {len(cards)} · '
    f'{card["exam_part"]} · {card["topic"]}'
)


# -------------------------------------------------------------------
# Flashcard
# -------------------------------------------------------------------

with st.container(border=True):
    card_heading_col, bookmark_col = st.columns([4, 1])

    with card_heading_col:
        st.markdown("### Question")

    with bookmark_col:
        bookmark_icon = "★" if card["is_bookmarked"] else "☆"

        if st.button(
            bookmark_icon,
            key=f'bookmark_{card["id"]}',
            use_container_width=True,
            help=(
                "Remove bookmark"
                if card["is_bookmarked"]
                else "Bookmark this card"
            ),
        ):
            set_bookmark(
                card["id"],
                not bool(card["is_bookmarked"]),
            )
            st.rerun()

    st.markdown(
        f"""
        <div style="
            padding: 1.25rem;
            border-radius: 0.75rem;
            background-color: rgba(128, 128, 128, 0.10);
            font-size: 1.1rem;
            line-height: 1.6;
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
        st.markdown("### Answer")

        st.markdown(
            f"""
            <div style="
                padding: 1.25rem;
                border-radius: 0.75rem;
                background-color: rgba(46, 160, 67, 0.12);
                font-size: 1.05rem;
                line-height: 1.6;
            ">
                {card["answer"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        reference_link(card)

        st.markdown("#### How well did you know it?")

        confidence_columns = st.columns(4)

        confidence_options = [
            ("Again", "Review again"),
            ("Hard", "Difficult"),
            ("Good", "Understood"),
            ("Easy", "Mastered"),
        ]

        for column, (label, help_text) in zip(
            confidence_columns,
            confidence_options,
        ):
            with column:
                if st.button(
                    label,
                    use_container_width=True,
                    key=f'confidence_{label}_{card["id"]}',
                    help=help_text,
                ):
                    set_confidence(card["id"], label)
                    st.toast(f"Confidence saved as {label}")

                    if st.session_state.flash_index < len(cards) - 1:
                        st.session_state.flash_index += 1

                    st.session_state.flash_show_answer = False
                    st.rerun()


# -------------------------------------------------------------------
# Navigation
# -------------------------------------------------------------------

st.write("")

previous_col, position_col, next_col = st.columns([1, 1.5, 1])

with previous_col:
    previous_disabled = st.session_state.flash_index == 0

    if st.button(
        "← Previous",
        use_container_width=True,
        disabled=previous_disabled,
    ):
        st.session_state.flash_index -= 1
        st.session_state.flash_show_answer = False
        st.rerun()


with position_col:
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


with next_col:
    next_disabled = st.session_state.flash_index >= len(cards) - 1

    if st.button(
        "Next →",
        use_container_width=True,
        disabled=next_disabled,
    ):
        st.session_state.flash_index += 1
        st.session_state.flash_show_answer = False
        st.rerun()


if st.session_state.flash_index == len(cards) - 1:
    st.success("You reached the end of this flashcard set! 🎉")