# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PyTorch and other libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create directories for ChromaDB and model cache
RUN mkdir -p /app/chroma_db /app/hf_cache

# Set environment variables
ENV PORT=8080
ENV CHROMA_DIR=/app/chroma_db
ENV CLIP_MODEL_NAME=clip-ViT-B-32
ENV HF_HOME=/app/hf_cache

# Pre-download CLIP model into the image to avoid download at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/clip-ViT-B-32', cache_folder='/app/hf_cache')"

# Expose port
EXPOSE 8080

# Run the application with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
