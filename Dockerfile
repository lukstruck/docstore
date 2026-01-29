FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    pandoc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Create data directory
RUN mkdir -p /app/data /app/cache

# Set environment
ENV DOCSTORE_DATA_DIR=/app/data
ENV DOCSTORE_CACHE_DIR=/app/cache
ENV DOCSTORE_HOST=0.0.0.0
ENV DOCSTORE_PORT=8420

EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8420/health || exit 1

CMD ["docstore", "serve"]
