FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Railway injects $PORT for the publicly exposed service.
# We run Streamlit on $PORT and FastAPI on a fixed internal 8000.
ENV BACKEND_PORT=8000
ENV BACKEND_URL=http://localhost:8000

# Expose Streamlit (Railway maps this to a public HTTPS URL)
EXPOSE 8501

# Start both services
CMD ["sh", "start.sh"]
