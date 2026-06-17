# Use a supported slim image with broad wheel availability for the RAG stack.
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Combine system updates and cleaning to reduce layer size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (leverages Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

RUN mkdir -p /app/data

# Explicitly copy the service account file
# COPY service-account.json /app/service-account.json

EXPOSE 5000

# Optimized for lower concurrency/single user usage
# Reduced workers (-w) to 2 or 4. 16 workers would consume massive RAM unnecessarily.
CMD ["gunicorn", "main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", \
     "--threads", "2", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "600", \
     "--log-level", "info"]
