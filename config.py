"""
config.py — Single source of truth for all configuration values.
All modules import from here; none read os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (local development)
load_dotenv()

# --- LLM ---
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

# --- Data ---
TITANIC_CSV_PATH: str = os.getenv("TITANIC_CSV_PATH", "titanic.csv")

# --- Backend ---
BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_URL: str = os.getenv("BACKEND_URL", f"http://localhost:{BACKEND_PORT}")

# --- CORS ---
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:8501",  # Streamlit default port
    "http://localhost:8000",
    "*",
]
