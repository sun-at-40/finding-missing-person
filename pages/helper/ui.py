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
/* Leave room for Streamlit's fixed top toolbar (about 3.75rem tall) */
.block-container { padding-top: 4.5rem; }
.app-header {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; flex-wrap: wrap;
    padding: 0.9rem 1.4rem; margin-bottom: 1.2rem;
    border-radius: 14px; color: #fff;
    background: linear-gradient(120deg, #0d2b6b 0%, #1565c0 60%, #1e88e5 100%);
    box-shadow: 0 4px 16px rgba(21, 101, 192, 0.30);
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
    background: #fff; color: #0d47a1; font-weight: 700;
    border-radius: 999px; padding: 2px 10px; font-size: 0.78rem;
}
.app-header .dot { width: 8px; height: 8px; border-radius: 50%; background: #69f0ae; }
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
