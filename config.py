"""
config.py — works for both local dev and split deployment.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TITANIC_CSV_PATH = os.getenv("TITANIC_CSV_PATH", "titanic.csv")
BACKEND_PORT     = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))

# Streamlit Cloud reads this to know where FastAPI is.
# Set it to your Railway public URL in Streamlit Cloud secrets.
BACKEND_URL = os.getenv("BACKEND_URL", f"http://localhost:{BACKEND_PORT}")