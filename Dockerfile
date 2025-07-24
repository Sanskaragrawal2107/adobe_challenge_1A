FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies optimized for performance
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the updated main.py with interactive features
COPY main.py .

# Create input and output directories
RUN mkdir -p input output

# Set environment variables for optimal performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# Support both interactive and batch modes
CMD ["python", "main.py"]
