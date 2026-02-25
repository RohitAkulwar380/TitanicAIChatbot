"""
app.py — Streamlit host for a fully custom HTML/JS chat UI.
The UI is loaded from chat_ui.html — kept separate from Python so that
JavaScript syntax (regex, backslashes, braces) is never mangled by f-strings.
The backend URL is injected via a <script> tag prepended to the HTML.
"""

import streamlit as st
import streamlit.components.v1 as components
import threading
import time
import logging
import socket
import sys
import os

st.set_page_config(
    page_title="Titanic Chat",
    page_icon="🚢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config import BACKEND_URL, BACKEND_PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Start FastAPI once per process ───────────────────────────────────────────
def _port_is_bound(port: int) -> bool:
    """Returns True if something is already listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _start_backend() -> None:
    try:
        import uvicorn
        from backend.main import app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=BACKEND_PORT, log_level="warning")
    except Exception as e:
        logger.error(f"Backend thread error: {e}")


def _ensure_backend_running() -> None:
    if not _port_is_bound(BACKEND_PORT):
        t = threading.Thread(target=_start_backend, daemon=True)
        t.start()
        logger.info(f"Backend thread started on port {BACKEND_PORT}")
        time.sleep(2)
    else:
        logger.info(f"Backend already running on port {BACKEND_PORT} — skipping start")


_ensure_backend_running()


# ── Strip Streamlit chrome ────────────────────────────────────────────────────
st.markdown("""
<style>
  #MainMenu, footer, header, .stDeployButton { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #040d1a; }
  iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Load HTML and inject backend URL via a <script> tag ──────────────────────
html_path = os.path.join(os.path.dirname(__file__), "chatui.html")

try:
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
except FileNotFoundError:
    st.error(f"chat_ui.html not found at {html_path}. Make sure it is in the same directory as app.py.")
    st.stop()

# Prepend a <script> that sets window.BACKEND_URL before the rest of the HTML runs.
# This is safer than f-string injection — the URL is a plain string assignment.
url_injection = f'<script>window.BACKEND_URL = "{BACKEND_URL}";</script>\n'
html_with_url = url_injection + html_content

# ── Render ────────────────────────────────────────────────────────────────────
components.html(html_with_url, height=820, scrolling=False)