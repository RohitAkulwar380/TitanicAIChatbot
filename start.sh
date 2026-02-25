#!/bin/sh
# start.sh — Runs FastAPI on 8000, Streamlit on 8501, nginx on $PORT proxying both.
# /api/* → FastAPI (port 8000)
# /*     → Streamlit (port 8501)

# Install nginx if not present
if ! command -v nginx > /dev/null 2>&1; then
    apt-get update -qq && apt-get install -y -qq nginx
fi

PORT=${PORT:-8080}

# Write nginx config dynamically (uses actual $PORT value)
cat > /etc/nginx/nginx.conf << NGINX
worker_processes 1;
events { worker_connections 1024; }
http {
    server {
        listen ${PORT};

        location /api/ {
            proxy_pass http://127.0.0.1:8000/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
        }

        location / {
            proxy_pass http://127.0.0.1:8501;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_read_timeout 86400;
        }
    }
}
NGINX

echo "Starting FastAPI on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level warning &

echo "Starting Streamlit on port 8501..."
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false &

sleep 3

echo "Starting nginx on port ${PORT}..."
exec nginx -g "daemon off;"