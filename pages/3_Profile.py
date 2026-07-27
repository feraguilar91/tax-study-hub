from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from modules.profile import (
    get_days_until_exam,
    get_exam_date,
    get_exam_message,
    get_profile,
    has_passed_exam,
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
    "Personalize your dashboard and track your progress through "
    "the Enrolled Agent exams."
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

        exam_parts = [
            "EA Part 1",
            "EA Part 2",
            "EA Part 3",
        ]

        saved_exam_part = profile.get(
            "current_exam_part",
            "EA Part 1",
        )

        if saved_exam_part not in exam_parts:
            saved_exam_part = "EA Part 1"

        current_exam_part = st.selectbox(
            "Current EA exam focus",
            exam_parts,
            index=exam_parts.index(
                saved_exam_part
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
            part_1_passed=profile["part_1_passed"],
            part_2_passed=profile["part_2_passed"],
            part_3_passed=profile["part_3_passed"],
        )

        st.success(
            "Your profile has been saved."
        )

        st.rerun()


# -------------------------------------------------------------------
# Enrolled Agent exam tab
# -------------------------------------------------------------------

with enrolled_agent_tab:
    st.subheader("EA Exam Progress")

    st.write(
        "Track which exams you have scheduled and which parts you have passed."
    )

    default_future_date = (
        date.today()
        + timedelta(days=60)
    )

    with st.form(
        "exam_progress_form"
    ):
        st.markdown(
            "### EA Part 1 — Individuals"
        )

        part_1_passed = st.checkbox(
            "I passed EA Part 1",
            value=profile["part_1_passed"],
        )

        part_1_enabled = st.checkbox(
            "I have scheduled EA Part 1",
            value=(
                profile["part_1_exam_date"]
                is not None
                and not profile["part_1_passed"]
            ),
            disabled=part_1_passed,
        )

        part_1_exam_date = st.date_input(
            "EA Part 1 exam date",
            value=(
                profile["part_1_exam_date"]
                or default_future_date
            ),
            disabled=(
                part_1_passed
                or not part_1_enabled
            ),
        )

        st.divider()

        st.markdown(
            "### EA Part 2 — Businesses"
        )

        part_2_passed = st.checkbox(
            "I passed EA Part 2",
            value=profile["part_2_passed"],
        )

        part_2_enabled = st.checkbox(
            "I have scheduled EA Part 2",
            value=(
                profile["part_2_exam_date"]
                is not None
                and not profile["part_2_passed"]
            ),
            disabled=part_2_passed,
        )

        part_2_exam_date = st.date_input(
            "EA Part 2 exam date",
            value=(
                profile["part_2_exam_date"]
                or default_future_date
            ),
            disabled=(
                part_2_passed
                or not part_2_enabled
            ),
        )

        st.divider()

        st.markdown(
            "### EA Part 3 — Representation"
        )

        part_3_passed = st.checkbox(
            "I passed EA Part 3",
            value=profile["part_3_passed"],
        )

        part_3_enabled = st.checkbox(
            "I have scheduled EA Part 3",
            value=(
                profile["part_3_exam_date"]
                is not None
                and not profile["part_3_passed"]
            ),
            disabled=part_3_passed,
        )

        part_3_exam_date = st.date_input(
            "EA Part 3 exam date",
            value=(
                profile["part_3_exam_date"]
                or default_future_date
            ),
            disabled=(
                part_3_passed
                or not part_3_enabled
            ),
        )

        exam_progress_submitted = st.form_submit_button(
            "Save EA Exam Progress",
            type="primary",
            use_container_width=True,
        )

    if exam_progress_submitted:
        save_profile(
            display_name=profile["display_name"],
            current_exam_part=profile["current_exam_part"],
            part_1_exam_date=(
                None
                if part_1_passed
                else (
                    part_1_exam_date
                    if part_1_enabled
                    else None
                )
            ),
            part_2_exam_date=(
                None
                if part_2_passed
                else (
                    part_2_exam_date
                    if part_2_enabled
                    else None
                )
            ),
            part_3_exam_date=(
                None
                if part_3_passed
                else (
                    part_3_exam_date
                    if part_3_enabled
                    else None
                )
            ),
            daily_card_goal=profile["daily_card_goal"],
            part_1_passed=part_1_passed,
            part_2_passed=part_2_passed,
            part_3_passed=part_3_passed,
        )

        st.success(
            "Your EA exam progress has been saved."
        )

        st.rerun()

    st.write("")

    st.subheader("Exam Status")

    exam_statuses = [
        (
            "EA Part 1",
            "Individuals",
            profile["part_1_exam_date"],
            profile["part_1_passed"],
        ),
        (
            "EA Part 2",
            "Businesses",
            profile["part_2_exam_date"],
            profile["part_2_passed"],
        ),
        (
            "EA Part 3",
            "Representation",
            profile["part_3_exam_date"],
            profile["part_3_passed"],
        ),
    ]

    status_columns = st.columns(
        3
    )

    for column, (
        exam_part,
        exam_name,
        exam_date,
        exam_passed,
    ) in zip(
        status_columns,
        exam_statuses,
    ):
        with column:
            with st.container(
                border=True
            ):
                st.markdown(
                    f"### {exam_part}"
                )

                st.caption(
                    exam_name
                )

                if exam_passed:
                    st.success(
                        "Passed",
                        icon="✅",
                    )

                    st.metric(
                        "Status",
                        "Complete",
                    )

                elif exam_date is not None:
                    days_until_exam = get_days_until_exam(
                        exam_date
                    )

                    st.info(
                        "Scheduled",
                        icon="📅",
                    )

                    st.metric(
                        "Exam date",
                        exam_date.strftime(
                            "%b %d, %Y"
                        ),
                    )

                    if days_until_exam is not None:
                        if days_until_exam < 0:
                            countdown_text = (
                                f"{abs(days_until_exam)} days ago"
                            )
                        elif days_until_exam == 0:
                            countdown_text = "Today"
                        else:
                            countdown_text = (
                                f"{days_until_exam} days"
                            )

                        st.metric(
                            "Countdown",
                            countdown_text,
                        )

                else:
                    st.warning(
                        "Not scheduled",
                        icon="○",
                    )

                    st.metric(
                        "Status",
                        "Not started",
                    )

    st.write("")

    st.subheader("Current Exam Focus")

    selected_exam_part = profile[
        "current_exam_part"
    ]

    selected_exam_passed = has_passed_exam(
        profile,
        selected_exam_part,
    )

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
        if selected_exam_passed:
            st.success(
                f"You have passed {selected_exam_part}. "
                "Update your current exam focus in the Profile tab "
                "when you are ready to study another part.",
                icon="🏆",
            )

        else:
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