# Stage 1: Build dependencies
FROM python:3.10-slim AS builder
WORKDIR /app

# Install system build dependencies (required for some memory packages like FAISS)
RUN apt-get update && apt-get install -y build-essential

COPY pyproject.toml .
# Create a dummy src structure for pip to install the package metadata
RUN mkdir -p src/cli && touch src/__init__.py src/cli/__init__.py src/cli/main.py

# Build wheels for core and memory dependencies
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels .
RUN pip install --upgrade pip setuptools wheel

RUN pip wheel --no-cache-dir --wheel-dir /app/wheels .

RUN pip wheel --no-cache-dir --wheel-dir /app/wheels ".[memory]" || true
# Stage 2: Runtime
FROM python:3.10-slim
WORKDIR /app

# Copy wheels from builder and install them
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy actual source code
COPY src/ /app/src/

# Pre-download the sentence-transformers model to cache it in the image (requires memory deps)
RUN python -c "try: \n\
    from sentence_transformers import SentenceTransformer \n\
    SentenceTransformer('all-mpnet-base-v2') \n\
except ImportError: \n\
    pass"

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["macr"]
