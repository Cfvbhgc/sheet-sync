FROM python:3.11-slim

WORKDIR /app

# install system deps (minimal — reportlab doesn't need much)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app code and data
COPY app/ ./app/
COPY data/ ./data/
COPY main.py .
COPY .env.example .env

# create output directory
RUN mkdir -p /app/output

# default command — generate monthly report
CMD ["python", "main.py", "--source", "data/sales_2024.csv", "--report", "monthly", "--format", "pdf", "--output", "/app/output"]
