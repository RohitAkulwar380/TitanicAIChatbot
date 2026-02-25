FROM python:3.11-slim

# Install system dependencies including nginx
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI internal port
ENV BACKEND_PORT=8000
# This gets overridden at runtime by Railway's $PORT
EXPOSE 8080

CMD ["sh", "start.sh"]