# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY models/ ./models/

# Create models directory if it doesn't exist
RUN mkdir -p models

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/train.py"]
