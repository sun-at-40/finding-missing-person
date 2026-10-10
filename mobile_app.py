import streamlit as st

from pages.helper import db_queries
from pages.helper.ui import render_header

st.set_page_config(
    page_title="Find Someone",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)
db_queries.create_db()

# st.navigation replaces the automatic pages/ sidebar (admin pages) with only
# the public pages below.
navigation = st.navigation(
    [
        st.Page(
            "mobile_pages/home.py",
            title="Find Someone",
            url_path="",
            default=True,
        ),
        st.Page(
            "mobile_pages/report_sighting.py",
            title="Report a Sighting",
            url_path="report-a-sighting",
        ),
        st.Page(
            "mobile_pages/pending_cases.py",
            title="Pending Cases",
            url_path="pending-cases",
        ),
        st.Page(
            "mobile_pages/solved_cases.py",
            title="Solved Cases",
            url_path="solved-cases",
        ),
    ],
    position="top",
)
render_header("Community", subtitle="Help us reunite families")
navigation.run()
