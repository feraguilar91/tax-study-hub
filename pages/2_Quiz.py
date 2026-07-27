from __future__ import annotations

import random

import streamlit as st

from modules.flashcards import (
    get_cards,
    get_filter_options,
)
from modules.progress_engine import record_result
from modules.ui import reference_link


st.set_page_config(
    page_title="Quiz | Tax Study Hub",
    page_icon="📝",
    layout="centered",
)

st.title("📝 Active-Recall Quiz")
st.caption(
    "Answer mentally or type notes, reveal the answer, then grade yourself."
)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


def start_quiz() -> None:
    pool = get_cards(
        exam_part=selected_part,
        topic=selected_topic,
    )

    random.shuffle(pool)

    st.session_state.quiz_cards = pool[
        : min(question_count, len(pool))
    ]
    st.session_state.quiz_index = 0
    st.session_state.quiz_show_answer = False
    st.session_state.quiz_notes = {}
    st.session_state.quiz_graded = {}


# -------------------------------------------------------------------
# Data and sidebar
# -------------------------------------------------------------------

parts, topics = get_filter_options()

with st.sidebar:
    st.header("Quiz setup")

    selected_part = st.selectbox(
        "EA exam part",
        ["All"] + parts,
    )

    selected_topic = st.selectbox(
        "Topic",
        ["All"] + topics,
    )

    question_count = st.slider(
        "Number of questions",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
    )


# -------------------------------------------------------------------
# Session state
# -------------------------------------------------------------------

study_session_id = st.session_state.get(
    "study_session_id"
)

setup_signature = (
    selected_part,
    selected_topic,
    question_count,
)

if (
    "quiz_cards" not in st.session_state
    or st.session_state.get("quiz_setup_signature")
    != setup_signature
):
    st.session_state.quiz_setup_signature = setup_signature
    start_quiz()


# -------------------------------------------------------------------
# Quiz controls
# -------------------------------------------------------------------

if st.button(
    "Start a new randomized quiz",
    use_container_width=True,
):
    start_quiz()
    st.rerun()


cards = st.session_state.quiz_cards

if not cards:
    st.warning(
        "No questions match the selected filters."
    )
    st.stop()


# -------------------------------------------------------------------
# Current question
# -------------------------------------------------------------------

st.session_state.quiz_index = min(
    st.session_state.quiz_index,
    len(cards) - 1,
)

st.session_state.quiz_index = max(
    st.session_state.quiz_index,
    0,
)

index = st.session_state.quiz_index
card = cards[index]

st.progress(
    (index + 1) / len(cards)
)

st.caption(
    f'Question {index + 1} of {len(cards)}'
    f' · {card["exam_part"]}'
    f' · {card["topic"]}'
)

st.markdown(
    "### Question"
)

st.info(
    card["question"]
)

notes_key = (
    f'quiz_notes_{card["id"]}'
)

st.text_area(
    "Optional: type your answer or notes",
    key=notes_key,
    height=120,
)


# -------------------------------------------------------------------
# Answer and grading
# -------------------------------------------------------------------

if st.session_state.quiz_show_answer:
    st.markdown(
        "### Correct answer"
    )

    st.success(
        card["answer"]
    )

    reference_link(
        card
    )

    grade = st.session_state.quiz_graded.get(
        card["id"]
    )

    if grade is None:
        correct_column, incorrect_column = st.columns(
            2
        )

        with correct_column:
            if st.button(
                "I got it right",
                type="primary",
                use_container_width=True,
                key=f'quiz_correct_{card["id"]}',
            ):
                record_result(
                    card["id"],
                    True,
                    session_id=study_session_id,
                )

                st.session_state.quiz_graded[
                    card["id"]
                ] = True

                st.rerun()

        with incorrect_column:
            if st.button(
                "I missed it",
                use_container_width=True,
                key=f'quiz_incorrect_{card["id"]}',
            ):
                record_result(
                    card["id"],
                    False,
                    session_id=study_session_id,
                )

                st.session_state.quiz_graded[
                    card["id"]
                ] = False

                st.rerun()

    elif grade:
        st.success(
            "Recorded as correct."
        )

    else:
        st.error(
            "Recorded as missed."
        )


# -------------------------------------------------------------------
# Navigation
# -------------------------------------------------------------------

previous_column, answer_column, next_column = st.columns(
    [1, 1.4, 1]
)

with previous_column:
    if st.button(
        "← Previous",
        disabled=(index == 0),
        use_container_width=True,
    ):
        st.session_state.quiz_index -= 1
        st.session_state.quiz_show_answer = False
        st.rerun()


with answer_column:
    answer_button_label = (
        "Hide Answer"
        if st.session_state.quiz_show_answer
        else "Show Answer"
    )

    if st.button(
        answer_button_label,
        type="primary",
        use_container_width=True,
        key=f'quiz_show_answer_{card["id"]}',
    ):
        st.session_state.quiz_show_answer = (
            not st.session_state.quiz_show_answer
        )

        st.rerun()


with next_column:
    if st.button(
        "Next →",
        disabled=(index >= len(cards) - 1),
        use_container_width=True,
    ):
        st.session_state.quiz_index += 1
        st.session_state.quiz_show_answer = False
        st.rerun()


# -------------------------------------------------------------------
# Quiz score
# -------------------------------------------------------------------

correct = sum(
    1
    for value in st.session_state.quiz_graded.values()
    if value is True
)

missed = sum(
    1
    for value in st.session_state.quiz_graded.values()
    if value is False
)

st.divider()

st.caption(
    f"Correct: {correct} · Missed: {missed}"
)