# NID Information Extraction API Documentation

## Overview
Production-ready RESTful API for extracting structured information from Bangladeshi National ID (NID) cards using PaddleOCR.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required. Can be added based on requirements.

---

## Endpoints

### 1. Health Check
Check if the API is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### 2. Extract NID Information
Extract structured information from NID card images.

**Endpoint:** `POST /api/v1/nid/extract`

**Content-Type:** `multipart/form-data`

**Request Parameters:**
- `nid_front` (file, required): Front side image of NID card
- `nid_back` (file, required): Back side image of NID card

**Supported Image Formats:** JPG, JPEG, PNG, BMP, TIFF

**Max File Size:** 10 MB per image

**Response (Success - 200):**
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

**Response (Error - 400/422/500):**
```json
{
  "status": "error",
  "message": "Error description",
  "processing_time_ms": 123.45,
  "errors": [
    {
      "field": "nid_front",
      "message": "Invalid file format",
      "type": "InvalidFileFormatError"
    }
  ],
  "timestamp": "2024-01-01T00:00:00"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/nid/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "nid_front=@/path/to/nid_front.jpg" \
  -F "nid_back=@/path/to/nid_back.jpg"
```

**Python Example:**
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

---

### 3. Get Metrics
Get application performance metrics and statistics.

**Endpoint:** `GET /metrics`

**Response:**
```json
{
  "performance": {
    "total_requests": 150,
    "successful_requests": 145,
    "failed_requests": 5,
    "average_processing_time_ms": "1234.56",
    "slow_requests_count": 2,
    "recent_slow_requests": []
  },
  "cache": {
    "cache_enabled": true,
    "cache_size": 50,
    "cache_max_size": 1000,
    "cache_ttl_seconds": 3600
  },
  "environment": "development",
  "version": "1.0.0"
}
```

---

### 4. Clear Cache
Clear all cached OCR results.

**Endpoint:** `POST /api/v1/cache/clear`

**Response:**
```json
{
  "status": "success",
  "message": "Cache cleared successfully",
  "entries_cleared": 50
}
```

---

### 5. API Root
Get API information and available endpoints.

**Endpoint:** `GET /`

**Response:**
```json
{
  "name": "NID Information Extraction API",
  "version": "1.0.0",
  "environment": "development",
  "status": "running",
  "docs_url": "/docs",
  "endpoints": {
    "health": "/health",
    "metrics": "/metrics",
    "nid_extraction": "/api/v1/nid/extract",
    "cache_clear": "/api/v1/cache/clear"
  }
}
```

---

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 400 | Bad Request (Invalid file format, file size exceeded) |
| 422 | Unprocessable Entity (Validation error, parsing error) |
| 429 | Too Many Requests (Rate limit exceeded) |
| 500 | Internal Server Error |

---

## Rate Limiting

- **Default Limit:** 100 requests per 60 seconds per IP address
- **Response Header:** `X-RateLimit-Remaining`
- **Error Response:** 429 Too Many Requests with retry information

---

## Response Headers

All responses include the following headers:
- `X-Request-ID`: Unique request identifier for tracking
- `X-Processing-Time-Ms`: Processing time in milliseconds
- `X-Content-Type-Options`: nosniff (Security)
- `X-Frame-Options`: DENY (Security)
- `X-XSS-Protection`: 1; mode=block (Security)

---

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs` (Development only)
- **ReDoc:** `http://localhost:8000/redoc` (Development only)

---

## Monitoring & Logging

### Structured Logging
All requests and errors are logged with structured JSON format including:
- Request ID
- Timestamp
- User agent
- Processing time
- Error details (if any)

### Performance Monitoring
- Automatic tracking of slow requests (>5 seconds)
- Request success/failure rates
- Average processing times
- Cache hit/miss statistics

### Log Location
Logs are stored in: `logs/app.log` with automatic rotation

---

## Best Practices

1. **Image Quality:** Use high-quality, well-lit images for better OCR accuracy
2. **File Size:** Compress images before upload to reduce processing time
3. **Error Handling:** Always check the `status` field in responses
4. **Rate Limiting:** Implement exponential backoff for retry logic
5. **Caching:** Identical images will be served from cache for faster response

---

## Configuration

Environment variables can be set in `.env` file:

```bash
# See .env.example for all available configuration options
DEBUG=False
LOG_LEVEL=INFO
ENABLE_CACHE=True
RATE_LIMIT_REQUESTS=100
```

---

## Support

For issues or questions:
1. Check logs in `logs/app.log`
2. Use `/metrics` endpoint to monitor performance
3. Enable DEBUG mode for detailed error messages
