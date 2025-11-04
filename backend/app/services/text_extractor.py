"""
Service for extracting text from various document formats.
"""
import os
from docx import Document as DocxDocument
from pypdf import PdfReader
from typing import Optional, List, Dict


class TextExtractor:
    """Extract text from documents."""
    
    async def extract_text_with_pages(self, file_path: str, file_type: str) -> List[Dict[str, any]]:
        """
        Extract text from a document file with page information.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (pdf, docx, doc, txt)
        
        Returns:
            List of dicts with 'page' number and 'content' text
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_type_lower = file_type.lower()
        
        if file_type_lower == "pdf":
            return await self._extract_from_pdf_with_pages(file_path)
        elif file_type_lower in ["docx", "doc"]:
            return await self._extract_from_docx_with_pages(file_path)
        elif file_type_lower == "txt":
            return await self._extract_from_txt_with_pages(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text from a document file (legacy method, concatenates all pages).
        
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
    
    async def _extract_from_pdf_with_pages(self, file_path: str) -> List[Dict[str, any]]:
        """Extract text from PDF with page numbers."""
        try:
            reader = PdfReader(file_path)
            pages = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    pages.append({"page": page_num, "content": text})
            return pages
        except Exception as e:
            raise ValueError(f"Error extracting PDF: {str(e)}")
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF (legacy, concatenates all)."""
        pages = await self._extract_from_pdf_with_pages(file_path)
        return "\n\n".join([p["content"] for p in pages])
    
    async def _extract_from_docx_with_pages(self, file_path: str) -> List[Dict[str, any]]:
        """Extract text from DOCX (no real page concept, treats whole doc as page 1)."""
        text = await self._extract_from_docx(file_path)
        return [{"page": 1, "content": text}]
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""
        try:
            doc = DocxDocument(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Error extracting DOCX: {str(e)}")
    
    async def _extract_from_txt_with_pages(self, file_path: str) -> List[Dict[str, any]]:
        """Extract text from TXT (no real page concept, treats whole file as page 1)."""
        text = await self._extract_from_txt(file_path)
        return [{"page": 1, "content": text}]
    
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

