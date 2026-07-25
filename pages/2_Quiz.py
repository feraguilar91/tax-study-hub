import random

import streamlit as st

from modules.database import (
    get_cards,
    get_filter_options,
    record_result,
)
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

parts, topics = get_filter_options()

with st.sidebar:
    st.header("Quiz setup")
    selected_part = st.selectbox("EA exam part", ["All"] + parts)
    selected_topic = st.selectbox("Topic", ["All"] + topics)
    question_count = st.slider("Number of questions", 5, 50, 10, 5)

setup_signature = (selected_part, selected_topic, question_count)

def start_quiz():
    pool = get_cards(
        exam_part=selected_part,
        topic=selected_topic,
    )
    random.shuffle(pool)
    st.session_state.quiz_cards = pool[: min(question_count, len(pool))]
    st.session_state.quiz_index = 0
    st.session_state.quiz_show_answer = False
    st.session_state.quiz_notes = {}
    st.session_state.quiz_graded = {}

if (
    "quiz_cards" not in st.session_state
    or st.session_state.get("quiz_setup_signature") != setup_signature
):
    st.session_state.quiz_setup_signature = setup_signature
    start_quiz()

if st.button("Start a new randomized quiz"):
    start_quiz()
    st.rerun()

cards = st.session_state.quiz_cards
if not cards:
    st.warning("No questions match the selected filters.")
    st.stop()

index = st.session_state.quiz_index
card = cards[index]

st.progress((index + 1) / len(cards))
st.caption(
    f'Question {index + 1} of {len(cards)} · '
    f'{card["exam_part"]} · {card["topic"]}'
)
st.markdown("### Question")
st.info(card["question"])

notes_key = f'quiz_notes_{card["id"]}'
st.text_area(
    "Optional: type your answer or notes",
    key=notes_key,
    height=120,
)

if st.session_state.quiz_show_answer:
    st.markdown("### Correct answer")
    st.success(card["answer"])
    reference_link(card)

    grade = st.session_state.quiz_graded.get(card["id"])
    if grade is None:
        correct_col, incorrect_col = st.columns(2)
        with correct_col:
            if st.button(
                "I got it right",
                type="primary",
                use_container_width=True,
            ):
                record_result(card["id"], True)
                st.session_state.quiz_graded[card["id"]] = True
                st.rerun()
        with incorrect_col:
            if st.button(
                "I missed it",
                use_container_width=True,
            ):
                record_result(card["id"], False)
                st.session_state.quiz_graded[card["id"]] = False
                st.rerun()
    elif grade:
        st.success("Recorded as correct.")
    else:
        st.error("Recorded as missed.")

previous_col, answer_col, next_col = st.columns([1, 1.4, 1])

with previous_col:
    if st.button(
        "← Previous",
        disabled=index == 0,
        use_container_width=True,
    ):
        st.session_state.quiz_index -= 1
        st.session_state.quiz_show_answer = False
        st.rerun()

with answer_col:
    label = (
        "Hide Answer"
        if st.session_state.quiz_show_answer
        else "Show Answer"
    )
    if st.button(label, type="primary", use_container_width=True):
        st.session_state.quiz_show_answer = (
            not st.session_state.quiz_show_answer
        )
        st.rerun()

with next_col:
    if st.button(
        "Next →",
        disabled=index >= len(cards) - 1,
        use_container_width=True,
    ):
        st.session_state.quiz_index += 1
        st.session_state.quiz_show_answer = False
        st.rerun()

correct = sum(
    1 for value in st.session_state.quiz_graded.values() if value is True
)
missed = sum(
    1 for value in st.session_state.quiz_graded.values() if value is False
)
st.divider()
st.caption(f"Correct: {correct} · Missed: {missed}")
