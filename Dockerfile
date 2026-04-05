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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for HF Spaces
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OPENENV_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from environment import AiSecurityEnv; env = AiSecurityEnv(); env.reset(); print('OK')" || exit 1

# Default command: run inference
CMD ["python", "inference.py"]
