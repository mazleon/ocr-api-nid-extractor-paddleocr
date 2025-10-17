"""
Main FastAPI application with NID information extraction endpoints.
"""
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.logger import logger, log_with_context
from app.schemas import (
    HealthCheckResponse,
    NIDExtractionData,
    NIDExtractionResponse,
    ErrorResponse,
    ErrorDetail,
    NIDFrontData,
    NIDBackData
)
from app.exceptions import (
    AppException,
    InvalidFileFormatError,
    FileSizeExceededError,
    OCRProcessingError
)
from app.services.ocr_service import get_ocr_service
from app.services.nid_parser import NIDParser
from app.middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    PerformanceMonitoringMiddleware
)

settings = get_settings()

# Performance monitoring instance (global for metrics access)
performance_monitor = PerformanceMonitoringMiddleware(None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize OCR service
    try:
        ocr_service = get_ocr_service()
        logger.info("OCR service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OCR service: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Clear cache
    if settings.ENABLE_CACHE:
        cache_cleared = ocr_service.clear_cache()
        logger.info(f"Cleared {cache_cleared} cache entries")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready API for extracting information from Bangladeshi National ID cards using PaddleOCR",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_REDOC else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_window=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
)

# Add performance monitoring (need to reassign to access metrics later)
performance_monitor = PerformanceMonitoringMiddleware(app)
app.middleware("http")(performance_monitor.dispatch)


# Exception Handlers

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    log_with_context(
        logger,
        "error",
        "Application exception occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        status_code=exc.status_code,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            message=exc.message,
            errors=[ErrorDetail(message=exc.message, type=type(exc).__name__)]
        ).model_dump(mode="json")
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    errors = [
        ErrorDetail(
            field=str(error.get("loc", ["unknown"])[1]) if len(error.get("loc", [])) > 1 else "unknown",
            message=error.get("msg", "Validation error"),
            type=error.get("type", "value_error")
        )
        for error in exc.errors()
    ]
    
    log_with_context(
        logger,
        "warning",
        "Request validation failed",
        path=request.url.path,
        errors=exc.errors()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            status="error",
            message="Request validation failed",
            errors=errors
        ).model_dump(mode="json")
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    log_with_context(
        logger,
        "warning",
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            message=str(exc.detail)
        ).model_dump(mode="json")
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    log_with_context(
        logger,
        "error",
        "Unexpected exception occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            message="An unexpected error occurred. Please try again later.",
            errors=[ErrorDetail(message=str(exc), type=type(exc).__name__)]
        ).model_dump(mode="json")
    )


# API Endpoints

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check() -> HealthCheckResponse:
    """
    Check if the service is healthy and running.
    
    Returns:
        Health status information
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )


@app.get(
    "/metrics",
    tags=["Monitoring"],
    summary="Get application metrics"
)
async def get_metrics() -> dict:
    """
    Get application performance metrics.
    
    Returns:
        Performance metrics and cache statistics
    """
    ocr_service = get_ocr_service()
    
    return {
        "performance": performance_monitor.get_metrics(),
        "cache": ocr_service.get_cache_stats(),
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION
    }


@app.post(
    "/api/v1/nid/extract",
    response_model=NIDExtractionResponse,
    tags=["NID Extraction"],
    summary="Extract information from NID cards",
    description="Upload front and back images of a Bangladeshi National ID card to extract structured information"
)
async def extract_nid_information(
    nid_front: Annotated[UploadFile, File(..., description="Front side of NID card")],
    nid_back: Annotated[UploadFile, File(..., description="Back side of NID card")]
) -> NIDExtractionResponse:
    """
    Extract structured information from NID card images.
    
    Args:
        nid_front: Front side image of NID card
        nid_back: Back side image of NID card
        
    Returns:
        Extracted NID information with processing metadata
        
    Raises:
        HTTPException: If processing fails
    """
    start_time = time.time()
    
    try:
        log_with_context(
            logger,
            "info",
            "Starting NID extraction",
            front_filename=nid_front.filename,
            back_filename=nid_back.filename,
            front_content_type=nid_front.content_type,
            back_content_type=nid_back.content_type
        )
        
        # Read image files
        front_bytes = await nid_front.read()
        back_bytes = await nid_back.read()
        
        # Validate file sizes
        if len(front_bytes) > settings.MAX_FILE_SIZE:
            raise FileSizeExceededError(
                f"Front image size ({len(front_bytes)} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        if len(back_bytes) > settings.MAX_FILE_SIZE:
            raise FileSizeExceededError(
                f"Back image size ({len(back_bytes)} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        # Get OCR service
        ocr_service = get_ocr_service()
        
        # Process front image
        front_ocr_result = ocr_service.extract_text(
            front_bytes,
            nid_front.filename or "nid_front.jpg"
        )
        
        if not front_ocr_result.success:
            raise OCRProcessingError(f"Failed to process front image: {front_ocr_result.error}")
        
        # Process back image
        back_ocr_result = ocr_service.extract_text(
            back_bytes,
            nid_back.filename or "nid_back.jpg"
        )
        
        if not back_ocr_result.success:
            raise OCRProcessingError(f"Failed to process back image: {back_ocr_result.error}")
        
        # Parse NID information
        front_data = NIDParser.parse_nid_front(front_ocr_result)
        back_data = NIDParser.parse_nid_back(back_ocr_result)
        
        # Calculate total processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build response
        response_data = NIDExtractionData(
            nid_front=front_data,
            nid_back=back_data,
        )
        
        log_with_context(
            logger,
            "info",
            "NID extraction completed successfully",
            processing_time_ms=f"{processing_time_ms:.2f}",
            fields_extracted={
                "name": bool(front_data.name),
                "dob": bool(front_data.date_of_birth),
                "nid_number": bool(front_data.nid_number),
                "address": bool(back_data.address)
            }
        )
        
        return NIDExtractionResponse(
            status="success",
            message="NID information extracted successfully",
            processing_time_ms=round(processing_time_ms, 2),
            data=response_data
        )
        
    except (InvalidFileFormatError, FileSizeExceededError, OCRProcessingError) as e:
        processing_time_ms = (time.time() - start_time) * 1000
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error during NID extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process NID images. Please try again."
        )


@app.post(
    "/api/v1/cache/clear",
    tags=["Cache Management"],
    summary="Clear OCR cache"
)
async def clear_cache() -> dict:
    """
    Clear all cached OCR results.
    
    Returns:
        Number of cache entries cleared
    """
    ocr_service = get_ocr_service()
    cleared_count = ocr_service.clear_cache()
    
    log_with_context(
        logger,
        "info",
        "Cache cleared via API",
        entries_cleared=cleared_count
    )
    
    return {
        "status": "success",
        "message": f"Cache cleared successfully",
        "entries_cleared": cleared_count
    }


@app.get(
    "/",
    tags=["Root"],
    summary="API root"
)
async def root() -> dict:
    """
    API root endpoint with basic information.
    
    Returns:
        API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "nid_extraction": "/api/v1/nid/extract",
            "cache_clear": "/api/v1/cache/clear"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
