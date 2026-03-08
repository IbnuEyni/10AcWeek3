# Document Intelligence Refinery - Production Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY rubric/ ./rubric/
COPY tests/ ./tests/

# Install dependencies
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e ".[all]"

# Create refinery directories
RUN mkdir -p .refinery/profiles .refinery/ldus .refinery/pageindex .refinery/figures

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Expose Streamlit port
EXPOSE 8501

# Default command: run Streamlit demo
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
