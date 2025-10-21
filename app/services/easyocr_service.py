"""
EasyOCR service for multilingual text extraction (Bengali and English).
Specialized for NID back image processing with address extraction.
"""
import hashlib
import time
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from typing import Optional, List, Tuple

import numpy as np
from PIL import Image
import easyocr

from app.config import get_settings
from app.logger import logger, log_with_context
from app.exceptions import OCRInitializationError, OCRProcessingError, InvalidFileFormatError
from app.schemas import EasyOCRResult, EasyOCRResponse


settings = get_settings()


class EasyOCRService:
    """
    Singleton EasyOCR service for multilingual text extraction.
    Optimized for Bengali and English text recognition in NID back images.
    """
    
    _instance: Optional['EasyOCRService'] = None
    _reader: Optional[easyocr.Reader] = None
    _cache: dict[str, EasyOCRResponse] = {}
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize EasyOCR service with configuration."""
        if self._reader is None:
            self._initialize_reader()
    
    def _initialize_reader(self) -> None:
        """Initialize EasyOCR reader with Bengali and English support."""
        try:
            logger.info("Initializing EasyOCR reader for Bengali and English...")
            
            # Initialize EasyOCR with Bengali ('bn') and English ('en')
            # Bengali is the primary language for NID back addresses
            # recog_network='standard' is faster than 'craft' for NID cards
            self._reader = easyocr.Reader(
                lang_list=['bn', 'en'],
                gpu=settings.EASYOCR_USE_GPU,
                model_storage_directory=settings.EASYOCR_MODEL_DIR,
                download_enabled=True,
                verbose=settings.DEBUG,
                quantize=True  # Enable quantization for faster inference
            )
            
            log_with_context(
                logger,
                "info",
                "EasyOCR reader initialized successfully",
                languages=['Bengali', 'English'],
                gpu_enabled=settings.EASYOCR_USE_GPU,
                model_dir=settings.EASYOCR_MODEL_DIR or "default (~/.EasyOCR/model)"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {str(e)}", exc_info=True)
            raise OCRInitializationError(f"EasyOCR initialization failed: {str(e)}")
    
    def _generate_cache_key(self, image_bytes: bytes) -> str:
        """
        Generate cache key from image content.
        
        Args:
            image_bytes: Image content as bytes
            
        Returns:
            SHA256 hash of image content
        """
        return hashlib.sha256(image_bytes).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[EasyOCRResponse]:
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
            logger.debug(f"EasyOCR cache hit for key: {cache_key[:16]}...")
            return self._cache[cache_key]
        
        logger.debug(f"EasyOCR cache miss for key: {cache_key[:16]}...")
        return None
    
    def _save_to_cache(self, cache_key: str, result: EasyOCRResponse) -> None:
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
            logger.debug(f"EasyOCR cache full, removed oldest entry: {oldest_key[:16]}...")
        
        self._cache[cache_key] = result
        logger.debug(f"EasyOCR cached result for key: {cache_key[:16]}...")
    
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
        use_cache: bool = True,
        detail: int = 1
    ) -> EasyOCRResponse:
        """
        Extract multilingual text from image using EasyOCR.
        Supports Bengali and English text recognition.
        
        Args:
            image_bytes: Image content as bytes
            filename: Original filename
            use_cache: Whether to use caching
            detail: Level of detail (0=text only, 1=text+bbox+confidence)
            
        Returns:
            EasyOCRResponse with extracted text and metadata
            
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
                        "Returning cached EasyOCR result",
                        filename=filename,
                        cache_key=cache_key[:16]
                    )
                    return cached_result
            
            # Convert bytes to PIL Image and preprocess
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed (faster than convert)
            if image.mode != 'RGB':
                if image.mode == 'RGBA':
                    # Create white background for RGBA
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Aggressive resizing for speed (NID cards don't need high resolution)
            # Reduce to optimal size for EasyOCR performance
            max_dim = settings.EASYOCR_MAX_IMAGE_DIMENSION or 1280  # Lower default for speed
            width, height = image.size
            largest_side = max(width, height)
            
            # Always resize if larger than optimal size
            if largest_side > max_dim:
                scale = max_dim / largest_side
                new_size = (int(width * scale), int(height * scale))
                # Use LANCZOS for better quality at smaller sizes, faster than BILINEAR for downscaling
                image = image.resize(new_size, Image.LANCZOS)
                if settings.DEBUG:
                    log_with_context(
                        logger,
                        "debug",
                        "Resized image for EasyOCR performance",
                        original_dimensions=f"{width}x{height}",
                        new_dimensions=f"{new_size[0]}x{new_size[1]}",
                        reduction_percent=f"{(1-scale)*100:.1f}%"
                    )
            
            # Convert PIL Image to numpy array (optimized)
            image_array = np.array(image, dtype=np.uint8)
            
            log_with_context(
                logger,
                "info",
                "Starting EasyOCR processing for NID back",
                filename=filename,
                image_size=len(image_bytes),
                image_dimensions=f"{image.width}x{image.height}",
                languages=['Bengali', 'English']
            )
            
            # Run EasyOCR with optimized parameters for speed
            # Returns list of tuples: (bbox, text, confidence)
            # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            results = self._reader.readtext(
                image_array,
                detail=detail,
                paragraph=settings.EASYOCR_PARAGRAPH_MODE,
                min_size=settings.EASYOCR_MIN_TEXT_SIZE,
                text_threshold=settings.EASYOCR_TEXT_THRESHOLD,
                low_text=settings.EASYOCR_LOW_TEXT_THRESHOLD,
                link_threshold=settings.EASYOCR_LINK_THRESHOLD,
                canvas_size=settings.EASYOCR_CANVAS_SIZE,
                mag_ratio=settings.EASYOCR_MAG_RATIO,
                slope_ths=0.1,  # Faster text detection
                ycenter_ths=0.5,  # Optimized for horizontal text
                height_ths=0.5,  # Optimized for NID text height
                width_ths=0.5,  # Optimized for NID text width
                add_margin=0.1,  # Smaller margin for speed
                batch_size=settings.EASYOCR_BATCH_SIZE  # Process multiple detections at once
            )
            
            # Parse results
            ocr_results = []
            all_texts_debug = []
            
            if detail == 1:
                # Format: (bbox, text, confidence)
                for bbox, text, confidence in results:
                    all_texts_debug.append(f"{text} ({confidence:.3f})")
                    
                    # Filter by confidence threshold
                    if confidence >= settings.EASYOCR_CONFIDENCE_THRESHOLD:
                        ocr_results.append(
                            EasyOCRResult(
                                text=text,
                                confidence=float(confidence),
                                bounding_box=bbox
                            )
                        )
            else:
                # Format: text only
                for text in results:
                    all_texts_debug.append(text)
                    ocr_results.append(
                        EasyOCRResult(
                            text=text,
                            confidence=1.0,  # No confidence when detail=0
                            bounding_box=None
                        )
                    )
            
            processing_time = (time.time() - start_time) * 1000
            
            response = EasyOCRResponse(
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
                "EasyOCR processing completed",
                filename=filename,
                texts_found=len(ocr_results),
                total_detected=len(all_texts_debug),
                processing_time_ms=f"{processing_time:.2f}"
            )
            
            # Debug: Log detected texts
            if settings.DEBUG and all_texts_debug:
                logger.debug(f"EasyOCR detected texts: {all_texts_debug[:10]}")  # First 10
            
            # Warn if no texts found
            if len(ocr_results) == 0 and len(all_texts_debug) > 0:
                log_with_context(
                    logger,
                    "warning",
                    "Texts detected but filtered by confidence threshold",
                    filename=filename,
                    threshold=settings.EASYOCR_CONFIDENCE_THRESHOLD,
                    detected_texts=all_texts_debug[:5]
                )
            
            return response
            
        except InvalidFileFormatError:
            raise
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"EasyOCR processing error: {str(e)}", exc_info=True)
            
            return EasyOCRResponse(
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
        logger.info(f"Cleared {count} EasyOCR cache entries")
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
            "service": "EasyOCR",
            "languages": ["Bengali", "English"]
        }


@lru_cache()
def get_easyocr_service() -> EasyOCRService:
    """
    Get singleton EasyOCR service instance.
    
    Returns:
        EasyOCRService instance
    """
    return EasyOCRService()
