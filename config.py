"""
config.py — Centralized configuration.
On Railway: Streamlit and FastAPI both run in the same container.
nginx proxies them through one public port:
  /api/* → FastAPI (port 8000)
  /*     → Streamlit (port 8501)

So BACKEND_URL must be the public Railway URL + /api
e.g. https://titanicaichatbot-production.up.railway.app/api
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Dataset ───────────────────────────────────────────────────────────────────
TITANIC_CSV_PATH = os.getenv("TITANIC_CSV_PATH", "titanic.csv")

# ── Backend ───────────────────────────────────────────────────────────────────
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# BACKEND_URL is used by the browser's JS to call the API.
# On Railway set this to: https://YOUR-APP.up.railway.app/api
# Locally it stays as: http://localhost:8000
BACKEND_URL = os.getenv("BACKEND_URL", f"http://localhost:{BACKEND_PORT}")