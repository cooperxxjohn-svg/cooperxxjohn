# Dockerfile for BOQ Estimation System
# Production-ready containerized deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY boq_schema.py .
COPY boq_calculator.py .
COPY boq_validator.py .
COPY drawing_extractor.py .
COPY boq_mapper.py .
COPY boq_estimator.py .
COPY config.py .
COPY api_server.py .

# Create necessary directories
RUN mkdir -p /app/temp_uploads /app/api_outputs /app/boq_output

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run API server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
