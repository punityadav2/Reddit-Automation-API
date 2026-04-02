# Use the official Playwright Python image — Chromium is pre-installed
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application source
COPY . .

# Create runtime directories
RUN mkdir -p data/sessions logs

EXPOSE 8000

# Use $PORT env var (set by Render/Railway) or fallback to 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
