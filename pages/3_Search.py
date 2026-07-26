import streamlit as st

from modules.flashcards import get_cards, get_filter_options

from modules.ui import reference_link

st.set_page_config(
    page_title="Search | Tax Study Hub",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Search the Tax Library")

parts, topics = get_filter_options()

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search = st.text_input(
        "Search questions, answers, or topics",
        placeholder="Example: basis, installment agreement, QBI",
    )
with col2:
    selected_part = st.selectbox("EA exam part", ["All"] + parts)
with col3:
    selected_topic = st.selectbox("Topic", ["All"] + topics)

cards = get_cards(
    exam_part=selected_part,
    topic=selected_topic,
    search=search.strip() or None,
)

st.caption(f"{len(cards)} matching cards")

for card in cards[:200]:
    with st.expander(
        f'{card["exam_part"]} · {card["topic"]} — {card["question"]}'
    ):
        st.markdown("**Answer**")
        st.write(card["answer"])
        reference_link(card)
        st.caption(f'Source file: {card["source_file"]}')

if len(cards) > 200:
    st.info("Showing the first 200 results. Add filters to narrow the list.")
