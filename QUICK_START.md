# Quick Start Guide - NID Information Extraction API

## ⚡ Fast Setup (5 minutes)

### Step 1: Install Dependencies
```bash
# Install required packages
uv pip install fastapi==0.115.5 'uvicorn[standard]==0.34.0' python-multipart==0.0.20 pydantic-settings==2.7.1 python-dotenv==1.0.1
```

### Step 2: Configure Environment
```bash
# Copy environment file (already done if .env exists)
cp .env.example .env

# Create logs directory
mkdir -p logs
```

### Step 3: Start the Server
```bash
# Option 1: Using the run script
./run.sh

# Option 2: Direct execution
python main.py

# Option 3: With uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Verify Installation
Open your browser and visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## 🧪 Test the API

### Using the Test Client

```bash
# Test with sample images
python test_api_client.py tests/sample_images/test_leon_front.jpeg tests/sample_images/test_leon_front.jpeg
```

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/nid/extract" \
  -F "nid_front=@path/to/nid_front.jpg" \
  -F "nid_back=@path/to/nid_back.jpg"
```

### Using Python Requests

```python
import requests

url = "http://localhost:8000/api/v1/nid/extract"
files = {
    'nid_front': open('nid_front.jpg', 'rb'),
    'nid_back': open('nid_back.jpg', 'rb')
}
response = requests.post(url, files=files)
print(response.json())
```

### Using Swagger UI

1. Go to http://localhost:8000/docs
2. Click on **POST /api/v1/nid/extract**
3. Click **"Try it out"**
4. Upload front and back images
5. Click **"Execute"**
6. View the response

---

## 📊 Monitor Performance

### Check Metrics
```bash
curl http://localhost:8000/metrics
```

### View Logs
```bash
tail -f logs/app.log
```

### Clear Cache (if needed)
```bash
curl -X POST http://localhost:8000/api/v1/cache/clear
```

---

## 🎯 Expected Response

**Success Response:**
```json
{
  "status": "success",
  "message": "NID information extracted successfully",
  "processing_time_ms": 1234.56,
  "data": {
    "nid_front": {
      "name": "JOHN DOE",
      "date_of_birth": "01/01/1990",
      "nid_number": "1234567890123",
      "raw_text": [
        "Name:",
        "JOHN DOE",
        "Date of Birth: 01/01/1990",
        "ID NO: 1234567890123"
      ]
    },
    "nid_back": {
      "address": "Village: ABC, Post: XYZ, Thana: DEF, District: GHI",
      "raw_text": [
        "Village: ABC",
        "Post: XYZ",
        "Thana: DEF",
        "District: GHI"
      ]
    }
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Invalid file format",
  "processing_time_ms": 12.34,
  "errors": [
    {
      "field": "nid_front",
      "message": "File format '.txt' not allowed",
      "type": "InvalidFileFormatError"
    }
  ]
}
```

---

## ⚙️ Common Configuration Changes

Edit `.env` file:

### Enable Debug Mode
```bash
DEBUG=True
LOG_LEVEL=DEBUG
```

### Disable Rate Limiting (for testing)
```bash
RATE_LIMIT_ENABLED=False
```

### Increase Cache Size
```bash
CACHE_MAX_SIZE=5000
```

### Change Port
```bash
PORT=8080
```

### Basic
```bash
DEBUG=True
LOG_LEVEL=DEBUG
ENABLE_DOCS=True
ENABLE_REDOC=True
```

### Performance
```bash
ENABLE_CACHE=True
CACHE_MAX_SIZE=5000
OCR_CONFIDENCE_THRESHOLD=0.3
```

### OCR
```bash
OCR_USE_GPU=False
```

---

## 🐛 Troubleshooting

### Issue: Port already in use
```bash
# Change port in .env
PORT=8080
```

### Issue: Models not downloading
```bash
# Check internet connection
# Models download automatically on first run (~200MB)
# Check logs/app.log for details
```

### Issue: Out of memory
```bash
# Reduce cache size in .env
CACHE_MAX_SIZE=100

# Or reduce max file size
MAX_FILE_SIZE=5242880  # 5MB
```

### Issue: Slow performance
```bash
# Enable caching
ENABLE_CACHE=True

# Reduce confidence threshold
OCR_CONFIDENCE_THRESHOLD=0.3

# Use GPU if available
OCR_USE_GPU=True
```

---

## 🚀 Next Steps

1. **Read Full Documentation**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Review Implementation**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
3. **Deploy with Docker**: See [Docker Deployment](#docker-deployment) below
4. **Integrate with Your App**: Use the API endpoints in your application

---

## 🐳 Docker Deployment

### Quick Docker Start
```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Access API at http://localhost:8000
```

### Manual Docker
```bash
# Build image
docker build -t nid-extraction-api .

# Run container
docker run -d -p 8000:8000 --name nid-api nid-extraction-api

# View logs
docker logs -f nid-api
```

---

## 📱 API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API docs |
| GET | `/metrics` | Performance metrics |
| POST | `/api/v1/nid/extract` | Extract NID info |
| POST | `/api/v1/cache/clear` | Clear cache |

---

## ✅ Verification Checklist

- [ ] Dependencies installed
- [ ] `.env` file created
- [ ] Server starts without errors
- [ ] Health check returns "healthy"
- [ ] API docs accessible at /docs
- [ ] Test extraction works
- [ ] Logs are being written
- [ ] Metrics endpoint responds

---

## 💡 Pro Tips

1. **First Request is Slow**: Models download on first run (~30s-60s)
2. **Use Caching**: Identical images return instantly from cache
3. **Monitor Metrics**: Check `/metrics` for performance insights
4. **Read Logs**: Structured JSON logs in `logs/app.log`
5. **Use Debug Mode**: Set `DEBUG=True` for development
6. **Test with Sample Images**: Use images in `tests/sample_images/`

---

## 📞 Getting Help

- Check logs: `logs/app.log`
- View metrics: http://localhost:8000/metrics
- Enable debug: Set `DEBUG=True` in `.env`
- Review docs: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

**You're all set! 🎉 Start extracting NID information!**
