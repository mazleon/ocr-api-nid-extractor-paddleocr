"""
PaddleOCR service with singleton pattern, caching, and error handling.
"""
import hashlib
import time
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from typing import Optional

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

from app.config import get_settings
from app.logger import logger, log_with_context
from app.exceptions import OCRInitializationError, OCRProcessingError, InvalidFileFormatError
from app.schemas import OCRResult, OCRResponse


settings = get_settings()


class OCRService:
    """
    Singleton OCR service with caching and performance optimization.
    Handles text extraction from images using PaddleOCR.
    """
    
    _instance: Optional['OCRService'] = None
    _ocr_engine: Optional[PaddleOCR] = None
    _cache: dict[str, OCRResponse] = {}
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize OCR service with configuration."""
        if self._ocr_engine is None:
            self._initialize_ocr()
    
    def _initialize_ocr(self) -> None:
        """Initialize PaddleOCR engine with configuration."""
        try:
            logger.info("Initializing PaddleOCR engine...")
            
            if settings.OCR_USE_GPU:
                log_with_context(
                    logger,
                    "warning",
                    "GPU execution requested via settings, but PaddleOCR pipeline no longer accepts 'use_gpu'. Falling back to CPU.",
                )

            self._ocr_engine = PaddleOCR(
                lang=settings.OCR_LANG,
                ocr_version=settings.OCR_VERSION,
                text_detection_model_name=settings.OCR_DET_MODEL,
                text_recognition_model_name=settings.OCR_REC_MODEL,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            
            log_with_context(
                logger, 
                "info", 
                "PaddleOCR engine initialized successfully",
                ocr_version=settings.OCR_VERSION,
                language=settings.OCR_LANG,
                gpu_enabled=settings.OCR_USE_GPU
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {str(e)}", exc_info=True)
            raise OCRInitializationError(f"OCR initialization failed: {str(e)}")
    
    def _generate_cache_key(self, image_bytes: bytes) -> str:
        """
        Generate cache key from image content.
        
        Args:
            image_bytes: Image content as bytes
            
        Returns:
            SHA256 hash of image content
        """
        return hashlib.sha256(image_bytes).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[OCRResponse]:
        """
        Retrieve OCR result from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached OCR response or None
        """
        if not settings.ENABLE_CACHE:
            return None
        
        if cache_key in self._cache:
            logger.debug(f"Cache hit for key: {cache_key[:16]}...")
            return self._cache[cache_key]
        
        logger.debug(f"Cache miss for key: {cache_key[:16]}...")
        return None
    
    def _save_to_cache(self, cache_key: str, result: OCRResponse) -> None:
        """
        Save OCR result to cache.
        
        Args:
            cache_key: Cache key
            result: OCR response to cache
        """
        if not settings.ENABLE_CACHE:
            return
        
        # Simple LRU: Remove oldest if cache is full
        if len(self._cache) >= settings.CACHE_MAX_SIZE:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache full, removed oldest entry: {oldest_key[:16]}...")
        
        self._cache[cache_key] = result
        logger.debug(f"Cached result for key: {cache_key[:16]}...")
    
    def _validate_image(self, image_bytes: bytes, filename: str) -> None:
        """
        Validate image file.
        
        Args:
            image_bytes: Image content
            filename: Original filename
            
        Raises:
            InvalidFileFormatError: If image format is invalid
        """
        # Check file extension
        extension = Path(filename).suffix.lower().lstrip(".")
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise InvalidFileFormatError(
                f"File format '.{extension}' not allowed. "
                f"Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Try to open image
        try:
            image = Image.open(BytesIO(image_bytes))
            image.verify()
        except Exception as e:
            logger.error(f"Invalid image file: {str(e)}")
            raise InvalidFileFormatError(f"Invalid image file: {str(e)}")
    
    def extract_text(
        self, 
        image_bytes: bytes, 
        filename: str,
        use_cache: bool = True
    ) -> OCRResponse:
        """
        Extract text from image using PaddleOCR.
        
        Args:
            image_bytes: Image content as bytes
            filename: Original filename
            use_cache: Whether to use caching
            
        Returns:
            OCRResponse with extracted text and metadata
            
        Raises:
            OCRProcessingError: If OCR processing fails
            InvalidFileFormatError: If image format is invalid
        """
        start_time = time.time()
        
        try:
            # Validate image
            self._validate_image(image_bytes, filename)
            
            # Check cache
            cache_key = self._generate_cache_key(image_bytes)
            if use_cache:
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    log_with_context(
                        logger,
                        "info",
                        "Returning cached OCR result",
                        filename=filename,
                        cache_key=cache_key[:16]
                    )
                    return cached_result
            
            # Convert bytes to PIL Image and preprocess
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed (handle RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL Image to numpy array (required by PaddleOCR)
            image_array = np.array(image)
            
            # Log image info for debugging
            if settings.DEBUG:
                logger.debug(f"Image mode: {image.mode}, size: {image.size}, array shape: {image_array.shape}")
            
            log_with_context(
                logger,
                "info",
                "Starting OCR processing",
                filename=filename,
                image_size=len(image_bytes),
                image_dimensions=f"{image.width}x{image.height}"
            )
            
            # Run OCR with numpy array
            results = list(self._ocr_engine.predict(image_array))
            
            # Debug: Log raw results structure
            if settings.DEBUG and results:
                logger.debug(f"OCR results count: {len(results)}")
                if len(results) > 0:
                    logger.debug(f"First result type: {type(results[0])}")
                    if hasattr(results[0], 'json'):
                        logger.debug(f"Result JSON keys: {list(results[0].json.keys())}")
            
            # Parse results
            ocr_results = []
            all_texts_debug = []
            if results:
                instance = results[0]
                res_json = instance.json.get("res", {})
                
                # Debug: Log what's in res_json
                if settings.DEBUG:
                    logger.debug(f"res_json keys: {list(res_json.keys())}")
                
                polys = res_json.get("rec_polys", [])
                texts = res_json.get("rec_texts", [])
                scores = res_json.get("rec_scores", [])
                
                # Debug: Log counts
                if settings.DEBUG:
                    logger.debug(f"Polys: {len(polys)}, Texts: {len(texts)}, Scores: {len(scores)}")
                
                # Debug: Log all detected texts
                for text, score in zip(texts, scores):
                    all_texts_debug.append(f"{text} ({float(score):.3f})")
                
                if settings.DEBUG and all_texts_debug:
                    logger.debug(f"All detected texts: {all_texts_debug}")
                
                for poly, text, score in zip(polys, texts, scores):
                    # Lower threshold or include all if debugging
                    threshold = 0.3 if settings.DEBUG else settings.OCR_CONFIDENCE_THRESHOLD
                    if float(score) >= threshold:
                        ocr_results.append(
                            OCRResult(
                                text=text,
                                confidence=float(score),
                                bounding_box=poly
                            )
                        )
            
            processing_time = (time.time() - start_time) * 1000
            
            response = OCRResponse(
                success=True,
                results=ocr_results,
                processing_time_ms=processing_time,
                error=None
            )
            
            # Cache result
            if use_cache:
                self._save_to_cache(cache_key, response)
            
            log_with_context(
                logger,
                "info",
                "OCR processing completed",
                filename=filename,
                texts_found=len(ocr_results),
                total_detected=len(all_texts_debug),
                processing_time_ms=f"{processing_time:.2f}"
            )
            
            # Warn if no texts found
            if len(ocr_results) == 0 and len(all_texts_debug) > 0:
                log_with_context(
                    logger,
                    "warning",
                    "Texts detected but filtered by confidence threshold",
                    filename=filename,
                    threshold=settings.OCR_CONFIDENCE_THRESHOLD,
                    detected_texts=all_texts_debug[:5]  # First 5 for brevity
                )
            
            return response
            
        except InvalidFileFormatError:
            raise
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"OCR processing error: {str(e)}", exc_info=True)
            
            return OCRResponse(
                success=False,
                results=[],
                processing_time_ms=processing_time,
                error=str(e)
            )
    
    def clear_cache(self) -> int:
        """
        Clear all cached OCR results.
        
        Returns:
            Number of cache entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_enabled": settings.ENABLE_CACHE,
            "cache_size": len(self._cache),
            "cache_max_size": settings.CACHE_MAX_SIZE,
            "cache_ttl_seconds": settings.CACHE_TTL_SECONDS
        }


@lru_cache()
def get_ocr_service() -> OCRService:
    """
    Get singleton OCR service instance.
    
    Returns:
        OCRService instance
    """
    return OCRService()
