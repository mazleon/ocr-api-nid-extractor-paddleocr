# Docker Deployment Guide

## Overview

This guide explains how to deploy the NID Information Extraction API using Docker with support for both PaddleOCR (front) and EasyOCR (back - Bengali/English).

## Features

- **Multi-stage Build**: Optimized image size
- **Model Caching**: Persistent volumes for OCR models
- **Health Checks**: Automatic container health monitoring
- **Resource Limits**: CPU and memory constraints
- **Security**: Non-root user execution
- **Auto-restart**: Automatic recovery from failures

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space (for models)

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Navigate to deployments directory
cd deployments

# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 2. Access the API

- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics

### 3. Test the API

```bash
# Test NID extraction
curl -X POST "http://localhost:8000/api/v1/nid/extract" \
  -F "nid_front=@nid_front.jpg" \
  -F "nid_back=@nid_back.jpg"
```

## Configuration

### Environment Variables

The docker-compose.yml includes all necessary environment variables:

#### Application Settings
```yaml
- APP_NAME=NID Information Extraction API
- DEBUG=False
- ENVIRONMENT=production
- HOST=0.0.0.0
- PORT=8000
- LOG_LEVEL=INFO
```

#### Cache Settings
```yaml
- ENABLE_CACHE=True
- CACHE_MAX_SIZE=5000
- CACHE_TTL_SECONDS=7200
```

#### PaddleOCR Settings (NID Front)
```yaml
- OCR_USE_GPU=False
- OCR_CONFIDENCE_THRESHOLD=0.3
- OCR_MAX_IMAGE_DIMENSION=640
```

#### EasyOCR Settings (NID Back - Bengali/English)
```yaml
- EASYOCR_USE_GPU=False
- EASYOCR_CONFIDENCE_THRESHOLD=0.25
- EASYOCR_MAX_IMAGE_DIMENSION=1280
- EASYOCR_MIN_TEXT_SIZE=8
- EASYOCR_TEXT_THRESHOLD=0.6
- EASYOCR_LOW_TEXT_THRESHOLD=0.3
- EASYOCR_LINK_THRESHOLD=0.3
- EASYOCR_CANVAS_SIZE=1920
- EASYOCR_BATCH_SIZE=10
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

## Volume Management

### Persistent Volumes

The deployment uses named volumes for model caching:

```yaml
volumes:
  - easyocr_models:/home/appuser/.EasyOCR/model
  - paddlex_models:/home/appuser/.paddlex/official_models
  - ./logs:/app/logs
```

### Benefits

- **Faster Startup**: Models downloaded once, reused across restarts
- **Reduced Network**: No repeated downloads
- **Persistence**: Models survive container recreation

### Managing Volumes

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect deployments_easyocr_models

# Remove volumes (will trigger re-download)
docker-compose down -v
```

## First Run

### Model Download Process

On first run, the container will download OCR models:

1. **PaddleOCR Models** (~100MB)
   - Detection model: PP-OCRv5_mobile_det
   - Recognition model: en_PP-OCRv5_mobile_rec

2. **EasyOCR Models** (~200MB)
   - Bengali detection model
   - Bengali recognition model
   - English recognition model

**Total**: ~300MB

**Time**: 2-5 minutes (depending on internet speed)

### Monitoring First Run

```bash
# Watch logs during first run
docker-compose logs -f nid-extraction-api

# Look for:
# - "Downloading model..."
# - "Model downloaded successfully"
# - "EasyOCR reader initialized successfully"
# - "PaddleOCR service initialized successfully"
```

## Health Checks

### Automatic Health Monitoring

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 120s  # Allows time for model downloads
```

### Check Container Health

```bash
# View health status
docker ps

# Detailed health info
docker inspect nid-extraction-api | grep -A 10 Health
```

## Production Deployment

### 1. Using Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Scale if needed (requires load balancer)
docker-compose up -d --scale nid-extraction-api=3
```

### 2. Using Docker Run

```bash
# Build image
docker build -f deployments/Dockerfile -t nid-extraction-api:latest .

# Run container
docker run -d \
  --name nid-extraction-api \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v easyocr_models:/home/appuser/.EasyOCR/model \
  -v paddlex_models:/home/appuser/.paddlex/official_models \
  -e ENVIRONMENT=production \
  -e ENABLE_CACHE=True \
  --restart unless-stopped \
  nid-extraction-api:latest
```

### 3. With GPU Support

```yaml
# Update docker-compose.yml
services:
  nid-extraction-api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - EASYOCR_USE_GPU=True
      - OCR_USE_GPU=True
```

**Requirements**:
- NVIDIA GPU
- nvidia-docker2 installed
- CUDA-compatible PyTorch in requirements.txt

## Monitoring

### View Logs

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f nid-extraction-api

# Filter by level
docker-compose logs | grep ERROR
```

### Resource Usage

```bash
# Container stats
docker stats nid-extraction-api

# Detailed info
docker inspect nid-extraction-api
```

### Application Metrics

```bash
# Health check
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics

# Cache stats
curl http://localhost:8000/api/v1/cache/stats
```

## Troubleshooting

### Container Won't Start

1. **Check logs**
   ```bash
   docker-compose logs nid-extraction-api
   ```

2. **Verify port availability**
   ```bash
   netstat -an | grep 8000
   ```

3. **Check resource limits**
   ```bash
   docker stats
   ```

### Models Not Downloading

1. **Check internet connectivity**
   ```bash
   docker exec nid-extraction-api ping -c 3 google.com
   ```

2. **Verify volume permissions**
   ```bash
   docker exec nid-extraction-api ls -la /home/appuser/.EasyOCR/model
   ```

3. **Manual download** (if needed)
   ```bash
   docker exec -it nid-extraction-api bash
   python -c "import easyocr; reader = easyocr.Reader(['bn', 'en'])"
   ```

### Slow Performance

1. **Enable GPU** (if available)
   ```yaml
   - EASYOCR_USE_GPU=True
   ```

2. **Increase resource limits**
   ```yaml
   limits:
     cpus: '4.0'
     memory: 8G
   ```

3. **Optimize settings**
   ```yaml
   - EASYOCR_MAX_IMAGE_DIMENSION=960
   - EASYOCR_CANVAS_SIZE=1280
   ```

### High Memory Usage

1. **Reduce batch size**
   ```yaml
   - EASYOCR_BATCH_SIZE=5
   ```

2. **Lower canvas size**
   ```yaml
   - EASYOCR_CANVAS_SIZE=1280
   ```

3. **Reduce cache size**
   ```yaml
   - CACHE_MAX_SIZE=1000
   ```

## Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Clear Cache

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/cache/clear

# Restart container (clears in-memory cache)
docker-compose restart
```

### Backup Models

```bash
# Backup volumes
docker run --rm \
  -v deployments_easyocr_models:/source \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/easyocr_models.tar.gz -C /source .

docker run --rm \
  -v deployments_paddlex_models:/source \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/paddlex_models.tar.gz -C /source .
```

### Restore Models

```bash
# Restore volumes
docker run --rm \
  -v deployments_easyocr_models:/target \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/easyocr_models.tar.gz -C /target

docker run --rm \
  -v deployments_paddlex_models:/target \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/paddlex_models.tar.gz -C /target
```

## Security

### Best Practices

1. **Non-root User**: Container runs as `appuser` (UID 1000)
2. **Read-only Filesystem**: Consider adding `read_only: true`
3. **Network Isolation**: Uses dedicated bridge network
4. **Resource Limits**: CPU and memory constraints
5. **Health Checks**: Automatic failure detection

### Production Hardening

```yaml
services:
  nid-extraction-api:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

## Performance Benchmarks

### Container Startup Time

- **Cold Start** (first run): 2-5 minutes (model downloads)
- **Warm Start** (cached models): 30-60 seconds
- **Restart**: 10-20 seconds

### Processing Time

- **NID Front** (PaddleOCR): 500-1000ms
- **NID Back** (EasyOCR): 800-1500ms
- **Total**: 1500-2500ms (first request)
- **Cached**: 10-50ms

### Resource Usage

- **Memory**: 2-3GB (normal), 4GB (peak)
- **CPU**: 50-100% during processing
- **Disk**: ~500MB (app + models)

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Review health: `docker ps`
3. Test API: `curl http://localhost:8000/health`
4. Check resources: `docker stats`

---

**Last Updated**: October 21, 2025
**Version**: 1.0.0
