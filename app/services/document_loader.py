import os
from typing import Dict, Any
from datetime import datetime, timezone
import io

from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import markdown
from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger(__name__)

class DocumentLoader:
    """Handles loading and extracting text from various document formats."""
    
    SUPPORTED_FORMATS = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.md': 'text/markdown'
    }
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            docx_file = io.BytesIO(file_content)
            doc = DocxDocument(docx_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except (OSError, ValueError, TypeError) as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}") from e
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from TXT file with encoding detection."""
        try:
            # Decode common text encodings without requiring an optional dependency.
            for encoding in ('utf-8-sig', 'utf-16', 'utf-32', 'cp1252'):
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = file_content.decode('utf-8', errors='ignore')
            return text.strip()
        except (UnicodeError, ValueError, TypeError) as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise ValueError(f"Failed to extract text from TXT: {str(e)}") from e
    
    @staticmethod
    def extract_text_from_markdown(file_content: bytes) -> str:
        """Extract text from Markdown file."""
        try:
            text = file_content.decode('utf-8', errors='ignore')
            # Convert markdown to HTML, then extract text
            html = markdown.markdown(text)
            soup = BeautifulSoup(html, 'html.parser')
            plain_text = soup.get_text()
            return plain_text.strip()
        except (UnicodeError, ValueError, TypeError) as e:
            logger.error(f"Error extracting text from Markdown: {str(e)}")
            raise ValueError(f"Failed to extract text from Markdown: {str(e)}") from e
    
    @staticmethod
    def extract_text(file_content: bytes, file_extension: str) -> str:
        """Extract text from file based on its extension."""
        extension = file_extension.lower()
        
        if extension == '.pdf':
            return DocumentLoader.extract_text_from_pdf(file_content)
        elif extension == '.docx':
            return DocumentLoader.extract_text_from_docx(file_content)
        elif extension == '.txt':
            return DocumentLoader.extract_text_from_txt(file_content)
        elif extension == '.md':
            return DocumentLoader.extract_text_from_markdown(file_content)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    @staticmethod
    def get_file_metadata(filename: str, file_size: int) -> Dict[str, Any]:
        """Extract metadata from file."""
        extension = os.path.splitext(filename)[1].lower()
        
        return {
            "filename": filename,
            "file_size": file_size,
            "file_type": DocumentLoader.SUPPORTED_FORMATS.get(extension, "unknown"),
            "extension": extension,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def validate_file(filename: str, content: bytes, max_size: int = 10485760) -> Dict[str, Any]:
        """
        Validate file size and type.
        
        Args:
            filename: Name of the file
            content: File content as bytes
            max_size: Maximum allowed file size in bytes (default 10MB)
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check file size
        file_size = len(content)
        if file_size > max_size:
            errors.append(f"File size {file_size} exceeds maximum allowed size of {max_size} bytes")
        
        # Check file extension
        extension = os.path.splitext(filename)[1].lower()
        if extension not in DocumentLoader.SUPPORTED_FORMATS:
            errors.append(f"Unsupported file format: {extension}. Supported formats: {', '.join(DocumentLoader.SUPPORTED_FORMATS.keys())}")
        
        # Check if file is empty
        if file_size == 0:
            errors.append("File is empty")
        
        # Check if file can be read
        if content and not errors:
            try:
                # Try to extract text to ensure file is valid
                DocumentLoader.extract_text(content, extension)
            except (OSError, ValueError, TypeError) as e:
                warnings.append(f"File may be corrupted: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "file_size": file_size,
            "extension": extension
        }
