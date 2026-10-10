import os

import streamlit as st

from pages.helper import db_queries

PAGE_SIZE = 10


def _fmt(dt):
    return dt.strftime("%d %b %Y, %H:%M") if dt else "Not recorded"


def show_case_list(status: str, title: str, empty_message: str):
    """List cases with the given status ("NF" pending, "F" solved)."""
    st.markdown(f'<div class="section-kicker">Community case board</div><h1>{title}</h1>', unsafe_allow_html=True)
    solved = status == "F"

    cases = db_queries.fetch_cases_by_status(status)
    search = st.text_input("Search by name, city or last seen location")
    if search.strip():
        q = search.strip().lower()
        cases = [
            c
            for c in cases
            if q in " ".join(str(v or "") for v in (c[1], c[3], c[4])).lower()
        ]

    if not cases:
        st.info(empty_message)
        return

    st.caption(f"{len(cases)} case(s)")
    pages = (len(cases) - 1) // PAGE_SIZE + 1
    key = f"mobile_page_{status}"
    page = (
        st.number_input("Page", 1, pages, 1, key=key) - 1 if pages > 1 else 0
    )

    for (
        case_id,
        name,
        age,
        city,
        last_seen,
        birth_marks,
        description,
        reported_on,
        solved_on,
        matched_with,
    ) in cases[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        if solved and not solved_on and matched_with:
            solved_on = db_queries.get_public_submission_time(matched_with)
        with st.container():
            st.markdown('<div class="case-card">', unsafe_allow_html=True)
            photo_col, info_col = st.columns([1, 3])
            photo_path = f"./resources/{case_id}.jpg"
            if os.path.exists(photo_path):
                photo_col.image(photo_path, width=140)
            else:
                photo_col.caption("No image")
            lines = [
                f"**{name}**, age {age}{', ' + city if city else ''}",
                f"- Last seen: {last_seen}",
                f"- Reported on: {_fmt(reported_on)}",
            ]
            if solved:
                lines.append(f"- Solved on: {_fmt(solved_on)}")
            if birth_marks:
                lines.append(f"- Birth marks: {birth_marks}")
            if description:
                lines.append(f"- Description: {description}")
            info_col.markdown("\n".join(lines))
            st.markdown("</div>", unsafe_allow_html=True)
