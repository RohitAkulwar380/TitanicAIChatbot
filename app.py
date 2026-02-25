"""
app.py — Streamlit Cloud frontend.
Loads chatui.html and injects BACKEND_URL (Railway FastAPI) via a script tag.
No thread startup — FastAPI runs separately on Railway.
"""

import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="Titanic Chat",
    page_icon="🚢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Read BACKEND_URL from environment ────────────────────────────────────────
# On Streamlit Cloud set this in App Settings → Secrets:
#   BACKEND_URL = "https://titanicaichatbot-production.up.railway.app"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ── Temporary debug line — shows which URL is being injected ─────────────────
# Remove this line once you confirm it's working
st.caption(f"API target: `{BACKEND_URL}`")

# ── Strip Streamlit chrome ───────────────────────────────────────────────────
st.markdown("""
<style>
  #MainMenu, footer, header, .stDeployButton { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }
  .stApp { background: #040d1a; }
  iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Load chatui.html ─────────────────────────────────────────────────────────
html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatui.html")

if not os.path.exists(html_path):
    st.error(f"chatui.html not found at: {html_path}")
    st.write("Files found:", os.listdir(os.path.dirname(os.path.abspath(__file__))))
    st.stop()

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Prepend a <script> that sets window.BACKEND_URL before anything else runs
url_script = f'<script>window.BACKEND_URL = "{BACKEND_URL}";</script>\n'
final_html = url_script + html_content

components.html(final_html, height=820, scrolling=False)