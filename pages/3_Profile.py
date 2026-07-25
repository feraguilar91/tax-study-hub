from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from modules.profile import (
    get_days_until_exam,
    get_exam_date,
    get_exam_message,
    get_profile,
    save_profile,
)


st.set_page_config(
    page_title="Profile & Exam Settings | Tax Study Hub",
    page_icon="⚙️",
    layout="wide",
)


profile = get_profile()


st.title("⚙️ Profile & Exam Settings")

st.caption(
    "Personalize your dashboard and track the time remaining "
    "before each Enrolled Agent exam."
)


profile_tab, enrolled_agent_tab = st.tabs(
    [
        "👤 Profile",
        "📝 Enrolled Agent Exams",
    ]
)


# -------------------------------------------------------------------
# Profile tab
# -------------------------------------------------------------------

with profile_tab:
    st.subheader("Your Profile")

    st.write(
        "Your display name will appear in the dashboard greeting."
    )

    with st.form(
        "profile_settings_form"
    ):
        display_name = st.text_input(
            "Display name",
            value=profile["display_name"],
            placeholder="Enter your name",
            help=(
                "This is the name shown in your dashboard greeting."
            ),
        )

        current_exam_part = st.selectbox(
            "Current EA exam focus",
            [
                "EA Part 1",
                "EA Part 2",
                "EA Part 3",
            ],
            index=[
                "EA Part 1",
                "EA Part 2",
                "EA Part 3",
            ].index(
                profile["current_exam_part"]
            ),
        )

        daily_card_goal = st.number_input(
            "Daily flashcard goal",
            min_value=1,
            max_value=500,
            value=profile["daily_card_goal"],
            step=5,
            help=(
                "The number of flashcards you would like to review each day."
            ),
        )

        profile_submitted = st.form_submit_button(
            "Save Profile",
            type="primary",
            use_container_width=True,
        )

    if profile_submitted:
        save_profile(
            display_name=display_name,
            current_exam_part=current_exam_part,
            part_1_exam_date=profile["part_1_exam_date"],
            part_2_exam_date=profile["part_2_exam_date"],
            part_3_exam_date=profile["part_3_exam_date"],
            daily_card_goal=int(
                daily_card_goal
            ),
        )

        st.success(
            "Your profile has been saved."
        )

        st.rerun()


# -------------------------------------------------------------------
# Enrolled Agent exam tab
# -------------------------------------------------------------------

with enrolled_agent_tab:
    st.subheader("EA Exam Schedule")

    st.write(
        "Enter an exam date for any part you are currently preparing for."
    )

    default_future_date = (
        date.today()
        + timedelta(days=60)
    )

    with st.form(
        "exam_date_form"
    ):
        part_1_enabled = st.checkbox(
            "I have scheduled EA Part 1",
            value=(
                profile["part_1_exam_date"]
                is not None
            ),
        )

        part_1_exam_date = st.date_input(
            "EA Part 1 exam date",
            value=(
                profile["part_1_exam_date"]
                or default_future_date
            ),
            disabled=not part_1_enabled,
        )

        st.divider()

        part_2_enabled = st.checkbox(
            "I have scheduled EA Part 2",
            value=(
                profile["part_2_exam_date"]
                is not None
            ),
        )

        part_2_exam_date = st.date_input(
            "EA Part 2 exam date",
            value=(
                profile["part_2_exam_date"]
                or default_future_date
            ),
            disabled=not part_2_enabled,
        )

        st.divider()

        part_3_enabled = st.checkbox(
            "I have scheduled EA Part 3",
            value=(
                profile["part_3_exam_date"]
                is not None
            ),
        )

        part_3_exam_date = st.date_input(
            "EA Part 3 exam date",
            value=(
                profile["part_3_exam_date"]
                or default_future_date
            ),
            disabled=not part_3_enabled,
        )

        exam_dates_submitted = st.form_submit_button(
            "Save Exam Dates",
            type="primary",
            use_container_width=True,
        )

    if exam_dates_submitted:
        save_profile(
            display_name=profile["display_name"],
            current_exam_part=profile["current_exam_part"],
            part_1_exam_date=(
                part_1_exam_date
                if part_1_enabled
                else None
            ),
            part_2_exam_date=(
                part_2_exam_date
                if part_2_enabled
                else None
            ),
            part_3_exam_date=(
                part_3_exam_date
                if part_3_enabled
                else None
            ),
            daily_card_goal=profile["daily_card_goal"],
        )

        st.success(
            "Your EA exam dates have been saved."
        )

        st.rerun()

    st.write("")

    st.subheader("Current Exam Countdown")

    selected_exam_part = profile[
        "current_exam_part"
    ]

    selected_exam_date = get_exam_date(
        profile,
        selected_exam_part,
    )

    days_remaining = get_days_until_exam(
        selected_exam_date
    )

    with st.container(
        border=True
    ):
        countdown_column, date_column = st.columns(
            2
        )

        with countdown_column:
            if days_remaining is None:
                countdown_value = "Not scheduled"
            elif days_remaining < 0:
                countdown_value = (
                    f"{abs(days_remaining)} days ago"
                )
            elif days_remaining == 0:
                countdown_value = "Today"
            else:
                countdown_value = (
                    f"{days_remaining} days"
                )

            st.metric(
                f"Time until {selected_exam_part}",
                countdown_value,
            )

        with date_column:
            exam_date_text = (
                selected_exam_date.strftime(
                    "%B %d, %Y"
                )
                if selected_exam_date
                else "No date entered"
            )

            st.metric(
                "Scheduled Date",
                exam_date_text,
            )

        if days_remaining is None:
            st.info(
                get_exam_message(
                    days_remaining
                ),
                icon="📅",
            )
        elif days_remaining < 0:
            st.warning(
                get_exam_message(
                    days_remaining
                ),
                icon="⚠️",
            )
        elif days_remaining <= 14:
            st.warning(
                get_exam_message(
                    days_remaining
                ),
                icon="⏳",
            )
        else:
            st.success(
                get_exam_message(
                    days_remaining
                ),
                icon="🎯",
            )


# -------------------------------------------------------------------
# Future account notice
# -------------------------------------------------------------------

st.write("")

with st.expander(
    "How will this work when the app is shared?"
):
    st.write(
        """
        This version stores one profile on the local computer running
        the app. Before public release, Tax Study Hub will need user
        authentication so each student has separate profile information,
        exam dates, bookmarks, review schedules, and progress.

        The profile structure added here prepares the app for that future
        multi-user system.
        """
    )