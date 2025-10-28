FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/
COPY static/ ./static/

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1

# This container will exit after the script runs
CMD ["python", "scripts/indexer.py", "index"]
