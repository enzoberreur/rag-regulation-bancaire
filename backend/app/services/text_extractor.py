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
    
    def _extract_real_page_number(self, page_content: str, physical_position: int) -> tuple[int, bool]:
        """
        Extrait le vrai numéro de page depuis le contenu du PDF (footer/header).
        
        Args:
            page_content: Contenu textuel de la page
            physical_position: Position physique dans le PDF (1-indexed)
        
        Returns:
            (page_number, is_extracted) - numéro de page et si c'est extrait ou physique
        """
        import re
        
        # Prendre les dernières lignes (footer) et premières lignes (header)
        lines = page_content.strip().split('\n')
        candidates = lines[:5] + lines[-5:]  # 5 premières + 5 dernières lignes
        
        for line in candidates:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: "Page X" ou "PAGE X" (le plus courant)
            match = re.search(r'\b(?:PAGE|Page|page)\s+(\d+)\b', line)
            if match:
                return int(match.group(1)), True
            
            # Pattern 2: "X/Y" ou "X / Y" (page X sur Y)
            match = re.search(r'\b(\d+)\s*/\s*\d+\b', line)
            if match and 1 <= int(match.group(1)) <= 1000:  # Limite raisonnable
                return int(match.group(1)), True
            
            # Pattern 3: "- X -" ou "– X –"
            match = re.search(r'[-–]\s*(\d+)\s*[-–]', line)
            if match and 1 <= int(match.group(1)) <= 1000:
                return int(match.group(1)), True
            
            # Pattern 4: "p. X" ou "p.X"
            match = re.search(r'\bp\.?\s*(\d+)\b', line, re.IGNORECASE)
            if match and 1 <= int(match.group(1)) <= 1000:
                return int(match.group(1)), True
            
            # Pattern 5: Ligne contenant juste un nombre (risqué, en dernier recours)
            if re.match(r'^\d+$', line):
                num = int(line)
                if 1 <= num <= 1000:
                    return num, True
        
        # Si aucun numéro trouvé, utiliser la position physique
        return physical_position, False
    
    async def _extract_from_pdf_with_pages(self, file_path: str) -> List[Dict[str, any]]:
        """Extract text from PDF with real page numbers."""
        try:
            reader = PdfReader(file_path)
            pages = []
            
            for physical_position, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    # Extraire le vrai numéro de page depuis le contenu
                    real_page_num, is_extracted = self._extract_real_page_number(text, physical_position)
                    
                    pages.append({
                        "page": real_page_num,
                        "content": text,
                        "physical_position": physical_position,
                        "page_extracted": is_extracted
                    })
                    
                    # Log pour debug
                    if is_extracted and real_page_num != physical_position:
                        print(f"   📄 Page physique {physical_position} → page réelle {real_page_num}")
            
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

