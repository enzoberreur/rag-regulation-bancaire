"""
Service for extracting text from various document formats.
"""
import os
from docx import Document as DocxDocument
from pypdf import PdfReader
from typing import Optional


class TextExtractor:
    """Extract text from documents."""
    
    async def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text from a document file.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (pdf, docx, doc, txt)
        
        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_type_lower = file_type.lower()
        
        if file_type_lower == "pdf":
            return await self._extract_from_pdf(file_path)
        elif file_type_lower in ["docx", "doc"]:
            return await self._extract_from_docx(file_path)
        elif file_type_lower == "txt":
            return await self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF."""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Error extracting PDF: {str(e)}")
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""
        try:
            doc = DocxDocument(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Error extracting DOCX: {str(e)}")
    
    async def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error extracting TXT: {str(e)}")

