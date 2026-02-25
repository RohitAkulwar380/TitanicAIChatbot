#!/bin/sh
# start.sh — Launch FastAPI in background, then Streamlit in foreground.
# Railway keeps the container alive as long as the foreground process runs.

echo "Starting FastAPI backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level warning &

# Give FastAPI a moment to bind before Streamlit starts
sleep 2

echo "Starting Streamlit on port ${PORT:-8501}..."
exec streamlit run app.py \
  --server.port=${PORT:-8501} \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
