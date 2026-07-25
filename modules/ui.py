from __future__ import annotations

import streamlit as st


def reset_navigation(prefix: str) -> None:
    st.session_state[f"{prefix}_index"] = 0
    st.session_state[f"{prefix}_show_answer"] = False


def navigation_buttons(prefix: str, total: int) -> None:
    index_key = f"{prefix}_index"
    answer_key = f"{prefix}_show_answer"

    previous, reveal, next_button = st.columns([1, 1.4, 1])

    with previous:
        if st.button(
            "← Previous",
            disabled=st.session_state[index_key] <= 0,
            use_container_width=True,
            key=f"{prefix}_previous",
        ):
            st.session_state[index_key] -= 1
            st.session_state[answer_key] = False
            st.rerun()

    with reveal:
        label = (
            "Hide Answer"
            if st.session_state[answer_key]
            else "Show Answer"
        )
        if st.button(
            label,
            type="primary",
            use_container_width=True,
            key=f"{prefix}_reveal",
        ):
            st.session_state[answer_key] = not st.session_state[answer_key]
            st.rerun()

    with next_button:
        if st.button(
            "Next →",
            disabled=st.session_state[index_key] >= total - 1,
            use_container_width=True,
            key=f"{prefix}_next",
        ):
            st.session_state[index_key] += 1
            st.session_state[answer_key] = False
            st.rerun()


def reference_link(card: dict) -> None:
    label = card.get("reference_label") or "IRS reference"
    url = card.get("reference_url")
    if url:
        st.markdown(f"**IRS reference:** [{label}]({url})")
    else:
        st.caption("No IRS reference has been assigned to this card yet.")
