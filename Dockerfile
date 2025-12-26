FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies (no cmake - not building C++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 5000

ENV FLASK_APP=homomorphic_face_encryption.app
ENV PYTHONPATH=/app/src

CMD ["flask", "run", "--host=0.0.0.0"]
