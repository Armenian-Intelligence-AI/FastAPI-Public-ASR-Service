# Use an official Python runtime as a parent image
FROM --platform=linux/arm64/v8 python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    supervisor \ 
    coreutils \
    ffmpeg

# Install Python dependencies
COPY requirements.txt .
COPY constraints.txt .

RUN pip3 install pyannote.audio==3.1.1 -c constraints.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Copy Supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY start_uvicorn.sh /app/start_uvicorn.sh
RUN chmod +x /app/start_uvicorn.sh

# Expose the FastAPI port
EXPOSE 8000

# Start supervisord to manage both FastAPI and Celery
CMD ["/usr/bin/supervisord"]