FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure storage directories exist and entrypoint has executable permissions
RUN mkdir -p data media/images media/audio static templates \
    && chmod +x docker-entrypoint.sh \
    && chmod -R 777 /app

# Expose ports: 8000 (Backend API & Web Portal), 8501 (Streamlit)
EXPOSE 8000 8501

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: start unified FastAPI backend (which also serves the web portal at /)
CMD ["sh", "-c", "uvicorn master_backend:app --host 0.0.0.0 --port ${PORT:-8000}"]
