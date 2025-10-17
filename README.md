# paddle-ocr-rnd - NID Extractor

## Description

Production-ready RESTful API for extracting structured information from Bangladeshi National ID (NID) cards using PaddleOCR and FastAPI.

## 🌟 Features

- **Intelligent OCR Processing**: Uses PaddleOCR V5 for high-accuracy text extraction
- **Structured Data Extraction**: Automatically extracts Name, Date of Birth, NID Number, Address, and returns full `raw_text` lists for both sides
- **Production-Ready**: 
  - Comprehensive error handling and validation
  - Request/response logging with structured JSON logs
  - Performance monitoring and metrics
  - Intelligent caching for faster responses
  - Rate limiting to prevent abuse
  - Security headers and middleware
- **Developer-Friendly**:
  - Auto-generated OpenAPI documentation
  - Type-safe with Pydantic models
  - Clear error messages
  - Health check endpoints
- **Deployment Ready**: Docker support with docker-compose

## 📋 Requirements

- Python 3.11+
- 10MB+ free disk space for models
- 2GB+ RAM recommended

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd paddle-ocr-rnd
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration (optional)
nano .env
```

### 4. Run the Application

**Option A: Using the run script (Recommended)**
```bash
chmod +x run.sh
./run.sh
```

**Option B: Direct Python execution**
```bash
python main.py
```

**Option C: Using Uvicorn directly**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the API
- **API Root**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs *(toggle via `ENABLE_DOCS`)*
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc *(toggle via `ENABLE_REDOC`)*
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f
## Contributing

