"""
Core services for OCR and NID parsing.
"""
from app.services.ocr_service import OCRService, get_ocr_service
from app.services.nid_parser import NIDParser

__all__ = ["OCRService", "get_ocr_service", "NIDParser"]
