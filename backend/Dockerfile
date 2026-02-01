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

# Copy and make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Run the application
CMD ["./start.sh"]
