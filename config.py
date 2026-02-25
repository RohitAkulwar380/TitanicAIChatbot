"""
config.py — Centralized configuration.
Reads from environment variables / .env file.
Works for both local development and Railway deployment.
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
# On Railway: FastAPI runs on a fixed internal port (8000), Streamlit on $PORT.
# The iframe JS hits BACKEND_URL — on Railway this must be the public URL
# since the iframe runs in the user's browser, not on the server.
#
# Set BACKEND_PUBLIC_URL in Railway environment variables to your Railway
# service's public URL (e.g. https://your-app.up.railway.app).
# FastAPI routes are served under /api/ via the reverse proxy in start.sh,
# OR you can expose FastAPI on a separate Railway service.
#
# For simplicity we proxy FastAPI through Streamlit's port using the
# PUBLIC_URL pattern — see start.sh for the nginx-free approach.

BACKEND_PORT       = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "")

# BACKEND_URL is what the browser's JS uses to call the API.
# - Locally:  http://localhost:8000  (browser and server are same machine)
# - Railway:  must be the public HTTPS URL of the service
BACKEND_URL = BACKEND_PUBLIC_URL or os.getenv("BACKEND_URL", f"http://localhost:{BACKEND_PORT}")