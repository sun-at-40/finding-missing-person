"""Shared look and feel: top header bar with logo, title and signed-in role."""

import html

import streamlit as st

TITLE = "Missing Person Identification System"

# Inline SVG so no image asset is needed: shield with a face and magnifier.
_LOGO = " ".join(
    line.strip()
    for line in """
<svg width="46" height="46" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <path d="M32 4 56 13v17c0 15-10 25-24 30C18 55 8 45 8 30V13z"
        fill="#ffffff" fill-opacity=".15" stroke="#ffffff" stroke-width="3"/>
  <circle cx="29" cy="26" r="7" fill="#ffffff"/>
  <path d="M16 46c1-8 6-12 13-12s12 4 13 12z" fill="#ffffff"/>
  <circle cx="42" cy="38" r="8" fill="none" stroke="#ffd54f" stroke-width="3.5"/>
  <path d="m48 44 7 7" stroke="#ffd54f" stroke-width="4" stroke-linecap="round"/>
</svg>
""".strip().splitlines()
)

_CSS = """
<style>
/* Shared foundation for the public and officer experiences. */
.block-container { padding-top: 4.8rem; max-width: 1180px; }
.stApp { background: #f5f7fb; }
.stMarkdown, .stTextInput, .stTextArea, .stSelectbox, .stFileUploader { color: #172033; }
.app-header {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; flex-wrap: wrap;
    padding: 0.9rem 1.4rem; margin-bottom: 1.2rem;
    border-radius: 14px; color: #fff;
    background: linear-gradient(120deg, #102a43 0%, #176b87 58%, #1f9d8b 100%);
    box-shadow: 0 8px 24px rgba(16, 42, 67, 0.18);
}
.app-header .brand { display: flex; align-items: center; gap: 0.9rem; }
.app-header .app-title { font-size: 1.35rem; font-weight: 700; line-height: 1.2; }
.app-header .app-sub { font-size: 0.8rem; opacity: 0.85; margin-top: 2px; }
.app-header .login-chip {
    display: flex; align-items: center; gap: 0.5rem;
    background: rgba(255,255,255,0.16); border-radius: 999px;
    padding: 0.35rem 0.9rem; font-size: 0.88rem; white-space: nowrap;
}
.app-header .role-badge {
    background: #fff; color: #176b87; font-weight: 700;
    border-radius: 999px; padding: 2px 10px; font-size: 0.78rem;
}
.app-header .dot { width: 8px; height: 8px; border-radius: 50%; background: #69f0ae; }
.section-kicker { color: #1f9d8b; text-transform: uppercase; letter-spacing: .12em;
    font-size: .72rem; font-weight: 800; margin-bottom: .35rem; }
.hero-panel { padding: 2.1rem 2.3rem; border-radius: 22px; color: white;
    background: linear-gradient(125deg, #102a43, #176b87 65%, #1f9d8b);
    box-shadow: 0 12px 30px rgba(16,42,67,.18); }
.hero-panel h1 { font-size: clamp(2rem, 5vw, 3.35rem); line-height: 1.05; margin: 0 0 .65rem; }
.hero-panel p { max-width: 680px; color: rgba(255,255,255,.83); font-size: 1.05rem; }
.stat-card { padding: 1.1rem 1.25rem; background: white; border: 1px solid #e6ebf2;
    border-radius: 16px; box-shadow: 0 5px 18px rgba(16,42,67,.06); }
.stat-card .value { color: #102a43; font-size: 1.8rem; font-weight: 800; }
.case-card { padding: 1rem; background: white; border: 1px solid #e6ebf2;
    border-radius: 16px; box-shadow: 0 5px 18px rgba(16,42,67,.05); }
</style>
"""


def render_header(role: str, name: str | None = None, subtitle: str | None = None):
    """Draw the top bar. role is shown as "Logged in as <role>"."""
    who = f"{html.escape(name)} · " if name else ""
    sub = f'<div class="app-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    # One unindented line: indented or blank-line HTML renders as a code block.
    markup = (
        f'<div class="app-header"><div class="brand">{_LOGO}'
        f'<div><div class="app-title">{TITLE}</div>{sub}</div></div>'
        f'<div class="login-chip"><span class="dot"></span>Logged in as {who}'
        f'<span class="role-badge">{html.escape(role)}</span></div></div>'
    )
    st.markdown(_CSS + markup, unsafe_allow_html=True)


def render_staff_header():
    """Header for the admin/officer app, using the signed-in user's role."""
    render_header(
        st.session_state.get("role", "Officer"),
        st.session_state.get("name"),
        "Officer & Admin Portal",
    )
