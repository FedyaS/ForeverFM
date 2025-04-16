# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend/
COPY backend/requirements.txt .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files from backend/
COPY backend/ .

# Expose port
EXPOSE 5001

# Run app
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "-b", "0.0.0.0:5001", "app:app"]