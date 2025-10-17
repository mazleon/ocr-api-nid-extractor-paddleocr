"""
Custom exceptions for the application.
"""


class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OCRInitializationError(AppException):
    """Raised when OCR engine fails to initialize."""
    def __init__(self, message: str = "Failed to initialize OCR engine"):
        super().__init__(message, status_code=500)


class OCRProcessingError(AppException):
    """Raised when OCR processing fails."""
    def __init__(self, message: str = "Failed to process image with OCR"):
        super().__init__(message, status_code=500)


class InvalidFileFormatError(AppException):
    """Raised when uploaded file format is invalid."""
    def __init__(self, message: str = "Invalid file format"):
        super().__init__(message, status_code=400)


class FileSizeExceededError(AppException):
    """Raised when uploaded file size exceeds limit."""
    def __init__(self, message: str = "File size exceeds maximum limit"):
        super().__init__(message, status_code=400)


class NIDParsingError(AppException):
    """Raised when NID information cannot be parsed."""
    def __init__(self, message: str = "Failed to parse NID information"):
        super().__init__(message, status_code=422)


class CacheError(AppException):
    """Raised when cache operations fail."""
    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(message, status_code=500)


class ValidationError(AppException):
    """Raised when request validation fails."""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)
