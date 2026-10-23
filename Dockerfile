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

# Ensure storage directories exist
RUN mkdir -p media/images media/audio

# Expose ports: 8000 (Backend API), 8501 (Frontend)
EXPOSE 8000 8501

# Default command: start FastAPI backend
CMD ["uvicorn", "master_backend:app", "--host", "0.0.0.0", "--port", "8000"]
