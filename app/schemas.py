"""
Pydantic schemas for request validation and response serialization.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")


class NIDFrontData(BaseModel):
    """Extracted data from NID front side."""
    name: Optional[str] = Field(None, description="Person's name")
    date_of_birth: Optional[str] = Field(None, description="Date of birth")
    nid_number: Optional[str] = Field(None, description="National ID number")
    raw_text: list[str] = Field(default_factory=list, description="All extracted text")


class NIDBackData(BaseModel):
    """Extracted data from NID back side."""
    address: Optional[str] = Field(None, description="Address in single line")
    raw_text: list[str] = Field(default_factory=list, description="All extracted text")


class NIDExtractionData(BaseModel):
    """Structured NID extraction result."""
    nid_front: NIDFrontData = Field(..., description="Extracted data from the NID front side")
    nid_back: NIDBackData = Field(..., description="Extracted data from the NID back side")


class NIDExtractionResponse(BaseModel):
    """Complete NID extraction API response."""
    status: str = Field(..., description="Response status: success or error")
    message: str = Field(..., description="Human-readable message")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    data: Optional[NIDExtractionData] = Field(None, description="Extracted NID data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "NID information extracted successfully",
                "processing_time_ms": 1234.56,
                "data": {
                    "nid_front": {
                        "name": "John Doe",
                        "date_of_birth": "01 Dec 1990",
                        "nid_number": "1234567890123",
                        "raw_text": [
                            "Name:",
                            "JOHN DOE",
                            "Date of Birth: 01 Dec 1990",
                            "ID NO: 1234567890123"
                        ]
                    },
                    "nid_back": {
                        "address": "123 Main St, City, Country",
                        "raw_text": [
                            "Village: ABC",
                            "Post: XYZ",
                            "Thana: DEF",
                            "District: GHI"
                        ]
                    }
                }
            }
        }


class ErrorDetail(BaseModel):
    """Error detail schema."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Error response schema."""
    status: str = Field(default="error", description="Response status")
    message: str = Field(..., description="Error message")
    processing_time_ms: Optional[float] = Field(None, description="Processing time if available")
    errors: Optional[list[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid file format",
                "processing_time_ms": 12.34,
                "errors": [
                    {
                        "field": "nid_front",
                        "message": "File format not supported",
                        "type": "ValueError"
                    }
                ],
                "timestamp": "2024-01-01T00:00:00"
            }
        }


class OCRResult(BaseModel):
    """OCR result for a single text detection."""
    text: str = Field(..., description="Detected text")
    confidence: float = Field(..., description="Detection confidence score")
    bounding_box: Optional[list[list[int]]] = Field(None, description="Bounding box coordinates")


class OCRResponse(BaseModel):
    """Complete OCR processing response."""
    success: bool = Field(..., description="Whether OCR was successful")
    results: list[OCRResult] = Field(default_factory=list, description="List of detected texts")
    processing_time_ms: float = Field(..., description="OCR processing time")
    error: Optional[str] = Field(None, description="Error message if any")


class EasyOCRResult(BaseModel):
    """EasyOCR result for a single text detection with multilingual support."""
    text: str = Field(..., description="Detected text (Bengali/English)")
    confidence: float = Field(..., description="Detection confidence score (0-1)")
    bounding_box: Optional[list[list[float]]] = Field(None, description="Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]")


class EasyOCRResponse(BaseModel):
    """Complete EasyOCR processing response for multilingual text extraction."""
    success: bool = Field(..., description="Whether OCR was successful")
    results: list[EasyOCRResult] = Field(default_factory=list, description="List of detected texts with Bengali/English support")
    processing_time_ms: float = Field(..., description="OCR processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if any")
