# Dockerfile for Render deployment
FROM python:3.11-slim

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY server.py .

# Expose port (Render sets PORT env var)
EXPOSE 10000

# Run the server
CMD gunicorn server:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4
