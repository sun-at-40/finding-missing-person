import os

import streamlit as st

from pages.helper import db_queries


def _fmt(dt):
    return dt.strftime("%d %b %Y") if dt else "Date not recorded"


st.markdown(
    """
    <div class="hero-panel">
      <div class="section-kicker" style="color:#9df0df">Community-powered search</div>
      <h1>Help bring someone home.</h1>
      <p>Browse active missing-person cases, share a sighting, and help families get answers faster.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

cases = db_queries.fetch_cases_by_status("NF")
solved_count = len(db_queries.fetch_cases_by_status("F"))
stat_a, stat_b, stat_c = st.columns(3)
for col, value, label in (
    (stat_a, len(cases), "Active cases"),
    (stat_b, solved_count, "Cases reunited"),
    (stat_c, "24/7", "Reports accepted"),
):
    col.markdown(
        f'<div class="stat-card"><div class="value">{value}</div><div>{label}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("### People who still need your help")
st.caption("If you recognise someone, use the button on their case to report a sighting.")

search = st.text_input(
    "Search active cases",
    placeholder="Search by name, city, or last seen location",
    label_visibility="collapsed",
)
if search.strip():
    query = search.strip().lower()
    cases = [
        case
        for case in cases
        if query in " ".join(str(value or "") for value in (case[1], case[3], case[4])).lower()
    ]

if not cases:
    st.info("No active cases match your search.")
else:
    for (
        case_id,
        name,
        age,
        city,
        last_seen,
        birth_marks,
        description,
        reported_on,
        _solved_on,
        _matched_with,
    ) in cases[:12]:
        with st.container():
            st.markdown('<div class="case-card">', unsafe_allow_html=True)
            photo_col, info_col, action_col = st.columns([1, 2.7, 1])
            photo_path = f"./resources/{case_id}.jpg"
            if os.path.exists(photo_path):
                photo_col.image(photo_path, width=150)
            else:
                photo_col.markdown("**Photo unavailable**")
            info_col.markdown(
                f"**{name}**  \n"
                f"Age {age or '—'} · {city or 'Location not recorded'}  \n"
                f"Last seen: **{last_seen or 'Not recorded'}**  \n"
                f"Reported {_fmt(reported_on)}"
            )
            if birth_marks or description:
                details = birth_marks or description
                info_col.caption(details)
            action_col.markdown(
                '<div style="color:#b45309;font-weight:700;margin-top:.7rem">● Still missing</div>',
                unsafe_allow_html=True,
            )
            if action_col.button("I have seen them", key=f"report_{case_id}", type="primary"):
                st.session_state["selected_sighting_case_id"] = case_id
                st.switch_page("mobile_pages/report_sighting.py")
            st.markdown("</div>", unsafe_allow_html=True)
