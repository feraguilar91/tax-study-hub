import streamlit as st

from modules.database import initialize_database
from modules.dashboard import get_dashboard_stats
from modules.session_engine import start_session

st.set_page_config(
    page_title="Tax Study Hub",
    page_icon="📚",
    layout="wide",
)

initialize_database()

if "study_session_id" not in st.session_state:
    st.session_state.study_session_id = start_session()

stats = get_dashboard_stats()

st.title("📚 Tax Study Hub")
st.subheader("Enrolled Agent exam study and practical tax reference")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Flashcards", stats["total_cards"])
col2.metric("Topics", stats["topics"])
col3.metric("EA Parts", stats["parts"])
col4.metric("Bookmarks", stats["bookmarks"])

st.markdown("### Flashcards by exam part")
for row in stats["by_part"]:
    st.write(f'**{row["exam_part"]}:** {row["card_count"]} cards')

st.markdown(
    """
    ### Start studying

    Use the sidebar to open:

    - **Flashcards** for guided review with Previous and Next navigation
    - **Quiz** for active recall and self-grading
    - **Search** to find cards by keyword or topic
    - **Progress** to review your activity
    """
)

st.info(
    "The source materials may contain rules or dollar amounts from a prior tax "
    "year. Use the linked IRS references to verify current law before applying "
    "a card to an actual taxpayer."
)
