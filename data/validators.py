"""
Validators for data operations.
"""

import os
import shutil
from pathlib import Path

# pylint: disable=import-error
try:
    import magic  # type: ignore
except ImportError:
    magic = None

from app.core.config import settings
from app.core.logging import logger


class DataValidator:
    """Validates data operations and file types."""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
    
    # MIME types for validation
    MIME_TYPES = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.md': 'text/markdown'
    }
    
    def __init__(self):
        self.max_file_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # Default 10MB
        self.allowed_extensions = self.ALLOWED_EXTENSIONS
        self.mime_types = self.MIME_TYPES
    
    def validate_file(self, filename: str, content: bytes) -> tuple:
        """
        Validate a file.
        
        Args:
            filename: Original filename
            content: File content as bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check filename
        if not filename:
            return (False, "No filename provided")
        
        # Check extension
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            return (False, f"Unsupported file type: {extension}. Allowed: {', '.join(self.allowed_extensions)}")
        
        # Check file size
        file_size = len(content)
        if file_size > self.max_file_size:
            return (False, f"File too large: {file_size} bytes (max: {self.max_file_size} bytes)")
        
        if file_size == 0:
            return (False, "Empty file")
        
        # Check MIME type if magic library is loaded successfully
        if magic is not None:
            try:
                mime_type = magic.from_buffer(content, mime=True)
                expected_mime = self.mime_types.get(extension)
                if expected_mime and mime_type and mime_type != expected_mime:
                    logger.warning("MIME type mismatch: %s vs %s", mime_type, expected_mime)
                    # Don't reject, just warn
            except getattr(magic, 'MagicException', Exception) as e:
                logger.warning("Could not validate MIME type: %s", e)
            except (TypeError, ValueError) as e:
                logger.warning("Invalid content for MIME validation: %s", e)
        else:
            logger.warning("MIME validation skipped: 'magic' library not available")
        
        return (True, None)
    
    def validate_filename(self, filename: str) -> bool:
        """Validate that filename is safe."""
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for dangerous characters
        dangerous_chars = [';', '|', '&', '$', '>', '<', '`']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        return True
    
    def get_safe_filename(self, filename: str) -> str:
        """Get a safe version of the filename."""
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove dangerous characters
        dangerous_chars = [';', '|', '&', '$', '>', '<', '`']
        for char in dangerous_chars:
            filename = filename.replace(char, '')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    def get_directory_size(self, directory: Path) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        if not directory.exists():
            return total
        
        for item in directory.rglob('*'):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except (OSError, FileNotFoundError, PermissionError) as e:
                    logger.warning("Could not access file %s: %s", item, e)
                    continue
        return total
    
    def check_disk_space(self, min_free_gb: float = 1.0) -> tuple:
        """
        Check if there's enough free disk space.
        
        Args:
            min_free_gb: Minimum free space in GB
        
        Returns:
            Tuple of (has_space, free_space_gb)
        """
        try:
            stat = shutil.disk_usage('/')
            free_gb = stat.free / (1024 ** 3)
            return (free_gb >= min_free_gb, free_gb)
        except (OSError, FileNotFoundError, PermissionError) as e:
            logger.error("Error checking disk space: %s", e)
            return (True, 999.0)  # Assume enough space on error
