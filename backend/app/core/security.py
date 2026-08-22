"""Security utilities for safe file handling and sanitization."""
import re
import os
from pathlib import Path
from ..core.exceptions import FileValidationError
from ..config import settings


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes an incoming file name to prevent path traversal and injection attacks.
    Removes directory traversal sequences and non-standard characters.
    """
    if not filename:
        raise FileValidationError("Filename cannot be empty.", code="EMPTY_FILENAME")
    
    # Strip any leading directory path
    base_name = os.path.basename(filename)
    
    # Normalize: keep only alphanumeric, underscore, hyphen, and period
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', base_name)
    
    if not clean_name or clean_name.startswith('.'):
        clean_name = f"upload_{clean_name.lstrip('.')}"
        
    return clean_name


def validate_file_size(file_size: int, max_size_bytes: int = None) -> None:
    """Validates raw byte size against maximum upload limits."""
    limit = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES
    if file_size == 0:
        raise FileValidationError("File is empty (0 bytes).", code="EMPTY_FILE")
    if file_size > limit:
        raise FileValidationError(
            f"File size ({file_size / (1024*1024):.2f} MB) exceeds the maximum allowed limit of {limit / (1024*1024):.2f} MB.",
            code="FILE_TOO_LARGE"
        )


def validate_file_path(file_path: str, max_size_bytes: int = None) -> Path:
    """
    Validates that a file path exists, is a regular file, has an allowed extension,
    and does not exceed the maximum allowed file size.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileValidationError(f"File not found or is not a valid regular file: {path.name}", code="FILE_NOT_FOUND")
    
    # Check extension
    if path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file extension '{path.suffix}'. Allowed extensions: {settings.ALLOWED_EXTENSIONS}",
            code="INVALID_EXTENSION"
        )
    
    # Check size
    limit = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES
    file_size = path.stat().st_size
    validate_file_size(file_size, limit)
        
    return path
