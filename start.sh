#!/bin/sh
# start.sh — FastAPI only. Streamlit runs on Streamlit Cloud.
echo "Starting FastAPI on port ${PORT:-8000}..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info