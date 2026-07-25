import streamlit as st

from modules.database import (
    get_cards,
    get_filter_options,
    record_view,
    set_bookmark,
    set_confidence,
)
from modules.ui import navigation_buttons, reference_link, reset_navigation

st.set_page_config(
    page_title="Flashcards | Tax Study Hub",
    page_icon="🃏",
    layout="centered",
)

st.title("🃏 Flashcards")

parts, topics = get_filter_options()

with st.sidebar:
    st.header("Study filters")
    selected_part = st.selectbox("EA exam part", ["All"] + parts)
    available_topics = topics
    selected_topic = st.selectbox("Topic", ["All"] + available_topics)
    bookmarked_only = st.checkbox("Bookmarked only")
    search = st.text_input("Search cards")

filter_signature = (
    selected_part,
    selected_topic,
    bookmarked_only,
    search.strip().lower(),
)

if st.session_state.get("flash_filter_signature") != filter_signature:
    st.session_state.flash_filter_signature = filter_signature
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

st.session_state.setdefault("flash_index", 0)
st.session_state.setdefault("flash_show_answer", False)
st.session_state.flash_index = min(st.session_state.flash_index, len(cards) - 1)

card = cards[st.session_state.flash_index]
view_key = f'flash_viewed_{card["id"]}'
if not st.session_state.get(view_key):
    record_view(card["id"])
    st.session_state[view_key] = True

st.caption(
    f'Card {st.session_state.flash_index + 1} of {len(cards)} · '
    f'{card["exam_part"]} · {card["topic"]}'
)

st.markdown("### Question")
st.info(card["question"])

if st.session_state.flash_show_answer:
    st.markdown("### Answer")
    st.success(card["answer"])
    reference_link(card)

    st.markdown("#### How well did you know it?")
    confidence_columns = st.columns(4)
    for column, label in zip(
        confidence_columns,
        ["Again", "Hard", "Good", "Easy"],
    ):
        with column:
            if st.button(
                label,
                use_container_width=True,
                key=f'confidence_{label}_{card["id"]}',
            ):
                set_confidence(card["id"], label)
                st.toast(f"Saved as {label}")

bookmark_label = (
    "Remove bookmark" if card["is_bookmarked"] else "Bookmark this card"
)
if st.button(bookmark_label, key=f'bookmark_{card["id"]}'):
    set_bookmark(card["id"], not bool(card["is_bookmarked"]))
    st.rerun()

navigation_buttons("flash", len(cards))
