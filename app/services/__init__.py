"""
Core services for OCR and NID parsing.
"""
from app.services.ocr_service import OCRService, get_ocr_service
from app.services.easyocr_service import EasyOCRService, get_easyocr_service
from app.services.nid_parser import NIDParser
from app.services.nid_back_parser import NIDBackParser

__all__ = [
    "OCRService", 
    "get_ocr_service", 
    "EasyOCRService", 
    "get_easyocr_service",
    "NIDParser",
    "NIDBackParser"
]
