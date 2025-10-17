# PaddleOCR Model Caching Guide

## Overview
PaddleOCR automatically downloads models on first run and caches them for subsequent use. This guide explains how to leverage model caching for improved performance.

## Default Behavior
By default, PaddleOCR downloads models to:
- **Linux/Mac**: `~/.paddlex/official_models/`
- **Windows**: `C:\Users\<username>\.paddlex\official_models\`

Models are automatically reused on subsequent runs.

## Configuration Options

### Environment Variables
Add these to your `.env` file to customize model cache locations:

```bash
# Optional: Specify custom model directories
OCR_DET_MODEL_DIR=/path/to/cache/PP-OCRv5_mobile_det
OCR_REC_MODEL_DIR=/path/to/cache/en_PP-OCRv5_mobile_rec
```

### Benefits of Custom Cache Directories
1. **Faster startup**: Skip download checks by pointing directly to model files
2. **Shared cache**: Multiple services can share the same model cache
3. **Docker optimization**: Mount pre-downloaded models into containers
4. **Offline deployment**: Pre-populate cache for air-gapped environments

## Local Development Setup

### Step 1: Locate Default Cache
After running the API once, check your default cache:
```bash
ls -la ~/.paddlex/official_models/
```

You should see directories like:
- `PP-OCRv5_mobile_det/`
- `en_PP-OCRv5_mobile_rec/`

### Step 2: (Optional) Use Custom Cache Location
Create a custom cache directory:
```bash
mkdir -p /opt/ocr-models
cp -r ~/.paddlex/official_models/* /opt/ocr-models/
```

Update `.env`:
```bash
OCR_DET_MODEL_DIR=/opt/ocr-models/PP-OCRv5_mobile_det
OCR_REC_MODEL_DIR=/opt/ocr-models/en_PP-OCRv5_mobile_rec
```

## Docker Deployment

### Option 1: Volume Mount (Recommended)
Mount your local cache into the container:

**docker-compose.yml**:
```yaml
services:
  nid-extraction-api:
    volumes:
      - ~/.paddlex/official_models:/root/.paddlex/official_models:ro
      - ./logs:/app/logs
```

This allows the container to use your pre-downloaded models.

### Option 2: Custom Cache Directory
1. Create a models directory:
```bash
mkdir -p ./models
cp -r ~/.paddlex/official_models/* ./models/
```

2. Update `deployments/.env`:
```bash
OCR_DET_MODEL_DIR=/app/models/PP-OCRv5_mobile_det
OCR_REC_MODEL_DIR=/app/models/en_PP-OCRv5_mobile_rec
```

3. Mount in docker-compose.yml:
```yaml
services:
  nid-extraction-api:
    volumes:
      - ./models:/app/models:ro
      - ./logs:/app/logs
```

### Option 3: Build Models Into Image
Add to your Dockerfile:
```dockerfile
# Copy pre-downloaded models
COPY ./models /root/.paddlex/official_models
```

Build with models included:
```bash
docker build -t nid-extraction-api .
```

## Performance Impact

### Without Cache Configuration
- **First run**: 30-60 seconds (downloads ~200MB models)
- **Subsequent runs**: 2-5 seconds (loads from default cache)

### With Custom Cache Configuration
- **First run**: 2-5 seconds (loads directly from specified directory)
- **Subsequent runs**: 2-5 seconds (consistent performance)

### Docker Without Volume Mount
- **Every container start**: 30-60 seconds (re-downloads models)

### Docker With Volume Mount
- **Every container start**: 2-5 seconds (uses mounted cache)

## Verification

### Check if Models are Cached
Look for these log messages on startup:
```
Model files already exist. Using cached files.
```

### Check Custom Directory Usage
If you configured custom directories, you'll see:
```json
{
  "message": "Using custom detection model directory",
  "model_dir": "/path/to/your/cache"
}
```

## Troubleshooting

### Models Re-downloading Every Time
**Cause**: Cache directory not accessible or incorrect path

**Solution**:
1. Verify path exists: `ls -la /path/to/cache`
2. Check permissions: `chmod -R 755 /path/to/cache`
3. Verify environment variable is set: `echo $OCR_DET_MODEL_DIR`

### Docker Container Slow Startup
**Cause**: Models not mounted or volume mount failed

**Solution**:
1. Verify volume mount: `docker inspect <container> | grep Mounts`
2. Check host path exists: `ls ~/.paddlex/official_models`
3. Ensure read permissions on host directory

### Model Version Mismatch
**Cause**: Cached models don't match configured model names

**Solution**:
1. Clear cache: `rm -rf ~/.paddlex/official_models`
2. Restart service to re-download correct models
3. Verify model names in `.env` match PaddleOCR expectations

## Best Practices

1. **Development**: Use default cache location (no configuration needed)
2. **Production**: Mount pre-downloaded models via volume for consistent startup times
3. **CI/CD**: Build models into Docker image for reproducible deployments
4. **Multi-service**: Share cache directory across services to save disk space
5. **Offline**: Pre-populate cache before deploying to air-gapped environments

## Example Configurations

### Development (.env)
```bash
# Use defaults - no configuration needed
# Models auto-download to ~/.paddlex/official_models/
```

### Production Docker (docker-compose.yml)
```yaml
services:
  nid-extraction-api:
    volumes:
      - /opt/ocr-models:/root/.paddlex/official_models:ro
    environment:
      - ENVIRONMENT=production
```

### Kubernetes (deployment.yaml)
```yaml
spec:
  containers:
    - name: nid-api
      volumeMounts:
        - name: ocr-models
          mountPath: /root/.paddlex/official_models
          readOnly: true
  volumes:
    - name: ocr-models
      persistentVolumeClaim:
        claimName: ocr-models-pvc
```

## Summary
- **Default behavior**: Models auto-cache to `~/.paddlex/official_models/`
- **Custom paths**: Set `OCR_DET_MODEL_DIR` and `OCR_REC_MODEL_DIR` for control
- **Docker**: Mount cache volumes to avoid re-downloading models
- **Performance**: Proper caching reduces startup from 30-60s to 2-5s
