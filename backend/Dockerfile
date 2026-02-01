FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /data

# Set environment variables
ENV DATABASE_PATH=/data/moltchess.db
ENV PYTHONUNBUFFERED=1

# Default port (Railway overrides via $PORT)
ENV PORT=8000
EXPOSE 8000

# Run the application (shell form to expand $PORT)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
