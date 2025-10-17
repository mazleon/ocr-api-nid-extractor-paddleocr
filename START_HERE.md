# 🚀 START HERE - NID Information Extraction API

## What is This?

A **production-ready API** for extracting structured information from Bangladeshi National ID (NID) cards:
- ✅ **Extracts**: Name, Date of Birth, NID Number, Address
- ✅ **Fast**: 500-2000ms per NID (with caching <10ms)
- ✅ **Robust**: Error handling, logging, monitoring
- ✅ **Secure**: Rate limiting, validation, security headers
- ✅ **Ready**: Docker support, auto-generated docs

---

## 🎯 Quick Start (3 Steps)

### 1️⃣ Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 2️⃣ Start the Server
```bash
./run.sh
```
*Or: `python main.py`*

### 3️⃣ Test It
Visit: **http://localhost:8000/docs**

---

## 📸 Try It Now

### Option A: Web Interface (Easiest)
1. Go to http://localhost:8000/docs
2. Click on **POST /api/v1/nid/extract**
3. Click **"Try it out"**
4. Upload 2 images (front & back of NID)
5. Click **"Execute"**
6. See extracted information! ✨

### Option B: Command Line
```bash
# Test with sample images
python test_api_client.py tests/sample_images/test_leon_front.jpeg tests/sample_images/test_leon_front.jpeg
```

### Option C: Python Code
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

## 📖 What You Get

**Input**: 2 NID card images (front & back)

**Output**: Structured JSON with:
```json
{
  "status": "success",
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
      "address": "Village: ABC, Post: XYZ, District: GHI",
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

---

## 🗂️ Project Structure

```
paddle-ocr-rnd/
├── app/                    # Application code
│   ├── main.py            # FastAPI app
│   ├── services/          # OCR & parsing services
│   └── ...                # Config, schemas, middleware
├── tests/                 # Test files & sample images
├── logs/                  # Application logs
├── main.py               # Run this to start
├── .env                  # Configuration
└── run.sh                # Easy start script
```

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **[QUICK_START.md](QUICK_START.md)** | Step-by-step setup guide |
| **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** | Complete API reference |
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | Technical details |
| **[README.md](README.md)** | Full documentation |

---

## 🎨 Key Features

### 🔍 Intelligent OCR
- Uses PaddleOCR V5 (latest)
- Multi-pattern text extraction
- Confidence-based filtering

### ⚡ Performance
- Result caching (10x faster)
- Singleton OCR engine
- Async processing

### 🛡️ Production-Ready
- Error handling & validation
- Rate limiting (100 req/min)
- Security headers
- Structured logging
- Performance monitoring

### 🚀 Easy Deployment
- Docker & Docker Compose
- Environment-based config
- Auto-generated API docs

---

## ⚙️ Configuration

Edit `.env` file:

```bash
# Basic
DEBUG=False
PORT=8000
ENABLE_DOCS=True
ENABLE_REDOC=True

# Performance
ENABLE_CACHE=True
CACHE_MAX_SIZE=1000

# Security
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100

# OCR
OCR_CONFIDENCE_THRESHOLD=0.3
OCR_USE_GPU=False
```

---

## 🐳 Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Access at http://localhost:8000
```

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

### Logs
```bash
tail -f logs/app.log
```

---

## 🔧 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/docs` | GET | Interactive API documentation |
| `/health` | GET | Health status |
| `/metrics` | GET | Performance metrics |
| `/api/v1/nid/extract` | POST | Extract NID information |
| `/api/v1/cache/clear` | POST | Clear cache |

---

## 🎯 Use Cases

1. **KYC Verification**: Automated identity verification
2. **Form Auto-fill**: Extract data for forms
3. **Data Entry**: Reduce manual typing
4. **Digital Onboarding**: Streamline customer onboarding
5. **Document Processing**: Batch NID processing

---

## 🐛 Troubleshooting

### Server won't start?
```bash
# Check logs
cat logs/app.log

# Try different port
# Edit .env: PORT=8080
```

### Slow performance?
```bash
# Enable caching (should be default)
# Edit .env: ENABLE_CACHE=True
```

### Poor accuracy?
- Use high-quality, well-lit images
- Ensure images are not blurry
- Use 300 DPI or higher resolution

---

## 💡 Tips

- **First request is slow** (~30s) - models download automatically
- **Identical images are cached** - instant response (<10ms)
- **Use debug mode** for development: `DEBUG=True`
- **Monitor metrics** to track performance
- **Check logs** for detailed error information

---

## 🤝 Support

- **Quick Guide**: [QUICK_START.md](QUICK_START.md)
- **API Reference**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Technical Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## ✅ Ready to Use!

1. ✅ Dependencies installed? → `uv pip install -r requirements.txt`
2. ✅ Server running? → `./run.sh` or `python main.py`
3. ✅ Tested? → Visit http://localhost:8000/docs

**You're all set! Start extracting NID information! 🎉**

---

## 📈 What's Next?

- [ ] Test with your NID images
- [ ] Integrate with your application
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Customize configuration

**Happy Extracting! 🚀**
