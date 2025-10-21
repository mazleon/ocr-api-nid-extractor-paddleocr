# EasyOCR Integration for NID Back Image Processing

## Overview

This document describes the integration of **EasyOCR** for processing NID (National ID) back images with **Bengali and English multilingual support**. The integration provides robust address extraction and text recognition capabilities for Bangladeshi National ID cards.

## Architecture

### Dual OCR Engine Strategy

The application now uses two OCR engines optimized for different purposes:

1. **PaddleOCR** - For NID front images (English-optimized)
   - Fast and accurate for English text
   - Extracts: Name, Date of Birth, NID Number

2. **EasyOCR** - For NID back images (Bengali/English multilingual)
   - Supports Bengali (বাংলা) and English text
   - Extracts: Address and other information in both languages

## Features

### EasyOCR Service (`easyocr_service.py`)

- **Multilingual Support**: Bengali (`bn`) and English (`en`)
- **Singleton Pattern**: Efficient resource management
- **Caching**: Built-in result caching for improved performance
- **Image Preprocessing**: Automatic resizing and format conversion
- **Configurable Parameters**: Fine-tune detection and recognition thresholds

### NID Back Parser (`nid_back_parser.py`)

- **Intelligent Address Extraction**: Recognizes Bengali and English address keywords
- **Text Cleaning**: Preserves Bengali Unicode characters (U+0980-U+09FF)
- **Multi-line Address Handling**: Combines address components into single line
- **Stop Word Detection**: Prevents over-collection of non-address text
- **Raw Text Access**: Returns all detected text for debugging

## Configuration

### Environment Variables (.env)

```bash
# EasyOCR Configuration
EASYOCR_USE_GPU=False                    # Enable GPU acceleration
EASYOCR_CONFIDENCE_THRESHOLD=0.3         # Minimum confidence score (0-1)
EASYOCR_MAX_IMAGE_DIMENSION=1920         # Max image dimension for processing
EASYOCR_PARAGRAPH_MODE=False             # Combine results into paragraphs
EASYOCR_MIN_TEXT_SIZE=10                 # Minimum text size in pixels
EASYOCR_TEXT_THRESHOLD=0.7               # Text detection threshold
EASYOCR_LOW_TEXT_THRESHOLD=0.4           # Low text threshold
EASYOCR_LINK_THRESHOLD=0.4               # Link threshold for text connection
EASYOCR_CANVAS_SIZE=2560                 # Canvas size for detection
EASYOCR_MAG_RATIO=1.0                    # Magnification ratio
```

### Configuration Class (`config.py`)

All EasyOCR settings are defined in the `Settings` class with sensible defaults:

```python
class Settings(BaseSettings):
    # EasyOCR Configuration
    EASYOCR_USE_GPU: bool = False
    EASYOCR_MODEL_DIR: str | None = None
    EASYOCR_CONFIDENCE_THRESHOLD: float = 0.3
    # ... more settings
```

## API Usage

### NID Extraction Endpoint

**Endpoint**: `POST /api/v1/nid/extract`

**Description**: Extracts structured information from NID front and back images using PaddleOCR (front) and EasyOCR (back).

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/nid/extract" \
  -F "nid_front=@nid_front.jpg" \
  -F "nid_back=@nid_back.jpg"
```

**Response**:
```json
{
  "status": "success",
  "message": "NID information extracted successfully",
  "processing_time_ms": 2345.67,
  "data": {
    "nid_front": {
      "name": "JOHN DOE",
      "date_of_birth": "01 Jan 1990",
      "nid_number": "1234567890123",
      "raw_text": ["Name:", "JOHN DOE", "Date of Birth: 01 Jan 1990", ...]
    },
    "nid_back": {
      "address": "গ্রাম: আবাদপুর, পোস্ট: রামপুর, থানা: সাভার, জেলা: ঢাকা",
      "raw_text": ["ঠিকানা", "গ্রাম: আবাদপুর", "পোস্ট: রামপুর", ...]
    }
  }
}
```

## Code Examples

### Using EasyOCR Service Directly

```python
from app.services.easyocr_service import get_easyocr_service

# Get service instance
easyocr_service = get_easyocr_service()

# Extract text from image
with open("nid_back.jpg", "rb") as f:
    image_bytes = f.read()

result = easyocr_service.extract_text(
    image_bytes=image_bytes,
    filename="nid_back.jpg",
    use_cache=True
)

# Access results
if result.success:
    for item in result.results:
        print(f"Text: {item.text}")
        print(f"Confidence: {item.confidence}")
        print(f"BBox: {item.bounding_box}")
```

### Using NID Back Parser

```python
from app.services.nid_back_parser import NIDBackParser

# Parse EasyOCR results
nid_back_data = NIDBackParser.parse_nid_back(easyocr_response)

print(f"Address: {nid_back_data.address}")
print(f"Raw texts: {nid_back_data.raw_text}")

# Get formatted text
formatted = NIDBackParser.get_formatted_text(
    easyocr_response, 
    separator="\n"
)
```

## Address Keywords

### Bengali Keywords
- ঠিকানা (Address)
- গ্রাম (Village)
- পোস্ট (Post)
- থানা (Thana)
- জেলা (District)
- বিভাগ (Division)
- উপজেলা (Upazila)

### English Keywords
- address
- village
- post
- thana
- district
- division
- upazila
- holding
- road
- ward

## Performance Optimization

### Caching Strategy

Both OCR services implement intelligent caching:

1. **Cache Key**: SHA256 hash of image bytes
2. **Cache Size**: Configurable max size (default: 1000 entries)
3. **LRU Eviction**: Oldest entries removed when cache is full
4. **Cache Clear**: API endpoint to clear all caches

### Image Preprocessing

- **Automatic Resizing**: Large images resized to max dimension
- **Format Conversion**: All images converted to RGB
- **Memory Efficient**: Processes images as numpy arrays

## Model Storage

### Default Locations

- **PaddleOCR Models**: `~/.paddlex/official_models/`
- **EasyOCR Models**: `~/.EasyOCR/model/`

### Automatic Download

Models are automatically downloaded on first use:
- Bengali detection model
- Bengali recognition model
- English recognition model

## Troubleshooting

### Common Issues

1. **Models Not Downloading**
   - Check internet connection
   - Verify write permissions to model directories
   - Check firewall settings

2. **Low Accuracy**
   - Adjust `EASYOCR_CONFIDENCE_THRESHOLD`
   - Increase `EASYOCR_CANVAS_SIZE` for larger images
   - Ensure good image quality (min 300 DPI recommended)

3. **Slow Performance**
   - Enable GPU: `EASYOCR_USE_GPU=True`
   - Reduce `EASYOCR_MAX_IMAGE_DIMENSION`
   - Enable caching: `ENABLE_CACHE=True`

4. **Bengali Text Not Detected**
   - Verify image contains clear Bengali text
   - Lower `EASYOCR_CONFIDENCE_THRESHOLD`
   - Check `EASYOCR_MIN_TEXT_SIZE` setting

## Testing

### Unit Tests

```python
# Test EasyOCR service
pytest tests/test_easyocr_service.py

# Test NID back parser
pytest tests/test_nid_back_parser.py
```

### Integration Tests

```python
# Test full NID extraction flow
pytest tests/test_nid_extraction.py
```

### Manual Testing

```bash
# Test with sample images
python test_api_client.py --front samples/nid_front.jpg --back samples/nid_back.jpg
```

## Monitoring

### Logs

EasyOCR operations are logged with context:

```json
{
  "timestamp": "2025-10-21T14:30:00",
  "level": "INFO",
  "message": "EasyOCR processing completed",
  "filename": "nid_back.jpg",
  "texts_found": 15,
  "bengali_texts": 10,
  "english_texts": 5,
  "processing_time_ms": 1234.56
}
```

### Metrics

- Processing time per image
- Cache hit/miss ratio
- Text detection count
- Language distribution (Bengali vs English)

## Best Practices

1. **Image Quality**: Use high-resolution images (min 300 DPI)
2. **File Format**: JPEG or PNG recommended
3. **File Size**: Keep under 10MB for optimal performance
4. **Caching**: Enable for production environments
5. **GPU**: Use GPU for high-volume processing
6. **Monitoring**: Track processing times and accuracy

## Future Enhancements

- [ ] Support for additional languages (Hindi, Urdu)
- [ ] Custom model training for NID-specific text
- [ ] Batch processing endpoint
- [ ] Real-time streaming OCR
- [ ] Advanced post-processing (spell check, validation)

## References

- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [EasyOCR Documentation](https://www.jaided.ai/easyocr/documentation)
- [Bengali Unicode Range](https://unicode.org/charts/PDF/U0980.pdf)
- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR)

## Support

For issues or questions:
1. Check logs in `logs/app.log`
2. Review configuration in `.env`
3. Test with sample images
4. Open GitHub issue with details

---

**Last Updated**: October 21, 2025
**Version**: 1.0.0
