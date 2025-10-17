"""
Custom middleware for logging, monitoring, and request handling.
"""
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status

from app.logger import logger, log_with_context
from app.config import get_settings

settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all HTTP requests and responses with timing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        
        log_with_context(
            logger,
            "info",
            "Incoming request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        # Process request
        try:
            response = await call_next(request)
            processing_time = (time.time() - start_time) * 1000
            
            # Log response
            log_with_context(
                logger,
                "info",
                "Request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                processing_time_ms=f"{processing_time:.2f}"
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time-Ms"] = f"{processing_time:.2f}"
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            
            log_with_context(
                logger,
                "error",
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                processing_time_ms=f"{processing_time:.2f}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware based on IP address.
    """
    
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.request_counts: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limits and process request.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or rate limit error
        """
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                req_time for req_time in self.request_counts[client_ip]
                if current_time - req_time < self.window_seconds
            ]
        else:
            self.request_counts[client_ip] = []
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_window:
            log_with_context(
                logger,
                "warning",
                "Rate limit exceeded",
                client_ip=client_ip,
                request_count=len(self.request_counts[client_ip]),
                limit=self.requests_per_window
            )
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after_seconds": self.window_seconds
                }
            )
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring application performance and metrics.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = {"total": 0, "success": 0, "error": 0}
        self.total_processing_time = 0.0
        self.slow_requests = []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Monitor request performance.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        if not settings.ENABLE_METRICS:
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            processing_time = (time.time() - start_time) * 1000
            
            # Update metrics
            self.request_counts["total"] += 1
            if 200 <= response.status_code < 400:
                self.request_counts["success"] += 1
            else:
                self.request_counts["error"] += 1
            
            self.total_processing_time += processing_time
            
            # Track slow requests (>5 seconds)
            if processing_time > 5000:
                self.slow_requests.append({
                    "path": request.url.path,
                    "method": request.method,
                    "processing_time_ms": processing_time,
                    "timestamp": time.time()
                })
                
                # Keep only last 100 slow requests
                if len(self.slow_requests) > 100:
                    self.slow_requests.pop(0)
                
                log_with_context(
                    logger,
                    "warning",
                    "Slow request detected",
                    path=request.url.path,
                    method=request.method,
                    processing_time_ms=f"{processing_time:.2f}"
                )
            
            return response
            
        except Exception as e:
            self.request_counts["total"] += 1
            self.request_counts["error"] += 1
            raise
    
    def get_metrics(self) -> dict:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary with metrics
        """
        avg_time = (
            self.total_processing_time / self.request_counts["total"]
            if self.request_counts["total"] > 0
            else 0
        )
        
        return {
            "total_requests": self.request_counts["total"],
            "successful_requests": self.request_counts["success"],
            "failed_requests": self.request_counts["error"],
            "average_processing_time_ms": f"{avg_time:.2f}",
            "slow_requests_count": len(self.slow_requests),
            "recent_slow_requests": self.slow_requests[-10:]  # Last 10
        }
