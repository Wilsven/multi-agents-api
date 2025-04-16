# Use an official Python 3.12 runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UV_NO_CACHE 1

# Install uv using the recommended multi-stage copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy only the dependency definition files first
COPY pyproject.toml uv.lock* ./
# If you don't use a lock file:
# COPY pyproject.toml ./

# Install Python dependencies using uv pip sync
RUN uv sync --system --no-cache pyproject.toml

# Copy the rest of the application code
COPY . .

# Make port 8000 available (adjust if your API uses a different port)
EXPOSE 8000

# Run uvicorn with live reload
CMD ["make", "run-server"]
