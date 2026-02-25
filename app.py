"""
app.py — Streamlit frontend for Railway deployment.
FastAPI is started separately by start.sh — this file is UI only.
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
import sys
import os

st.set_page_config(
    page_title="Titanic Chat",
    page_icon="🚢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config import BACKEND_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Strip Streamlit chrome ────────────────────────────────────────────────────
st.markdown("""
<style>
  #MainMenu, footer, header, .stDeployButton { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #040d1a; }
  iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Load HTML and inject backend URL ─────────────────────────────────────────
html_path = os.path.join(os.path.dirname(__file__), "chatui.html")

try:
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
except FileNotFoundError:
    st.error(f"chatui.html not found at {html_path}.")
    st.stop()

# Inject backend URL as a global JS variable before the HTML runs
url_injection = f'<script>window.BACKEND_URL = "{BACKEND_URL}";</script>\n'
html_with_url = url_injection + html_content

components.html(html_with_url, height=820, scrolling=False)