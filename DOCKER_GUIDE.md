# Docker Deployment Guide

## Quick Start

### 1. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

Access the Streamlit demo at: http://localhost:8501

### 2. Build and Run with Docker

```bash
# Build the image
docker build -t document-intelligence-refinery .

# Run the container
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.refinery:/app/.refinery \
  -e GEMINI_API_KEY=your_key_here \
  document-intelligence-refinery
```

### 3. Run Tests in Docker

```bash
# Run tests with docker-compose
docker-compose --profile test run test

# Or with docker directly
docker run --rm \
  -v $(pwd)/tests:/app/tests \
  document-intelligence-refinery \
  pytest tests/ -v
```

## Environment Variables

Create a `.env` file:

```bash
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Volume Mounts

- `./data:/app/data` - Input documents
- `./.refinery:/app/.refinery` - Output artifacts (profiles, LDUs, PageIndex)
- `./.env:/app/.env` - Environment variables

## Production Deployment

### AWS ECS

```bash
# Build for ARM64 (Graviton)
docker buildx build --platform linux/arm64 -t refinery:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag refinery:latest <account>.dkr.ecr.us-east-1.amazonaws.com/refinery:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/refinery:latest
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-intelligence-refinery
spec:
  replicas: 2
  selector:
    matchLabels:
      app: refinery
  template:
    metadata:
      labels:
        app: refinery
    spec:
      containers:
      - name: refinery
        image: document-intelligence-refinery:latest
        ports:
        - containerPort: 8501
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: refinery-secrets
              key: gemini-api-key
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: refinery
          mountPath: /app/.refinery
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: refinery-data
      - name: refinery
        persistentVolumeClaim:
          claimName: refinery-artifacts
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs document-intelligence-refinery

# Interactive shell
docker run -it --entrypoint /bin/bash document-intelligence-refinery
```

### Permission issues

```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) .refinery/
```

### Out of memory

```bash
# Increase memory limit
docker run -m 4g -p 8501:8501 document-intelligence-refinery
```

## Performance Optimization

### Multi-stage build (smaller image)

```dockerfile
FROM python:3.10-slim as builder
WORKDIR /app
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"
COPY pyproject.toml .
RUN uv venv .venv && . .venv/bin/activate && uv pip install -e ".[all]"

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["streamlit", "run", "streamlit_app.py"]
```

### Cache dependencies

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t refinery .
```

## Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

## Security

### Non-root user

```dockerfile
RUN useradd -m -u 1000 refinery
USER refinery
```

### Scan for vulnerabilities

```bash
docker scan document-intelligence-refinery
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t refinery:${{ github.sha }} .
      - name: Run tests
        run: docker run refinery:${{ github.sha }} pytest tests/
```
