import streamlit as st

from modules.database import get_dashboard_stats

st.set_page_config(
    page_title="Progress | Tax Study Hub",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Progress")

stats = get_dashboard_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cards viewed", stats["views"])
col2.metric("Correct", stats["correct"])
col3.metric("Missed", stats["incorrect"])
col4.metric("Bookmarks", stats["bookmarks"])

attempts = stats["correct"] + stats["incorrect"]
accuracy = (stats["correct"] / attempts * 100) if attempts else 0

st.markdown("### Quiz accuracy")
st.metric("Accuracy", f"{accuracy:.1f}%")
st.progress(min(accuracy / 100, 1.0))

st.markdown("### Library size")
for row in stats["by_part"]:
    st.write(f'**{row["exam_part"]}:** {row["card_count"]} cards')
