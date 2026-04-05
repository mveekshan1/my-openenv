FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY environment.py .
COPY tasks.py .
COPY inference.py .
COPY openenv.yaml .
COPY README.md .
COPY server.py .
COPY app.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports for HF Spaces and API validation
EXPOSE 7860
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OPENENV_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from environment import AiSecurityEnv; env = AiSecurityEnv(); env.reset(); print('OK')" || exit 1

# Default command: run the OpenEnv API server for validation
# The OpenEnv submission checks target server.py for /reset and /step endpoints.
CMD ["python", "server.py"]
