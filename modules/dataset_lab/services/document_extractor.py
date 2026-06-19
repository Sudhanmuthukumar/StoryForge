import os
from pathlib import Path
from typing import Dict, Any

class DocumentExtractor:
    """Extracts raw text and basic metadata from PDF, DOCX, EPUB, and TXT files."""
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = path.suffix.lower()
        if ext == '.pdf':
            return self._extract_pdf(path)
        elif ext == '.docx':
            return self._extract_docx(path)
        elif ext == '.epub':
            return self._extract_epub(path)
        elif ext == '.txt':
            return self._extract_txt(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _clean_title(self, raw: str) -> str:
        """Cleans up filenames into readable titles."""
        return raw.replace('_', ' ').replace('-', ' ').title()

    def _extract_pdf(self, path: Path) -> Dict[str, Any]:
        import fitz  # PyMuPDF
        
        doc = fitz.open(str(path))
        
        # Prioritize filename over PDF metadata because omnibus PDFs often have overarching titles
        # or completely inaccurate embedded titles.
        filename_title = self._clean_title(path.stem)
        
        meta_title = doc.metadata.get("title", "")
        # If the meta title is vastly different from filename, fallback to filename
        if not meta_title or len(meta_title.split()) > 10 or meta_title.lower() == "untitled":
            title = filename_title
        else:
            title = filename_title # Safer fallback for Phase 1.5 Omnibus requirements
            
        author = doc.metadata.get("author", "Unknown")
        if not author or author.isspace():
            author = "Unknown"
        
        raw_text = []
        for page in doc:
            raw_text.append(page.get_text())
            
        return {
            "title": title,
            "author": author,
            "raw_text": "\n".join(raw_text)
        }

    def _extract_docx(self, path: Path) -> Dict[str, Any]:
        import docx
        
        doc = docx.Document(str(path))
        raw_text = [p.text for p in doc.paragraphs]
        
        filename_title = self._clean_title(path.stem)
        title = doc.core_properties.title
        if not title or title.isspace():
            title = filename_title
            
        author = doc.core_properties.author
        if not author or author.isspace():
            author = "Unknown"
        
        return {
            "title": title,
            "author": author,
            "raw_text": "\n".join(raw_text)
        }

    def _extract_epub(self, path: Path) -> Dict[str, Any]:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book = epub.read_epub(str(path))
        
        filename_title = self._clean_title(path.stem)
        title = filename_title
        author = "Unknown"
        
        title_meta = book.get_metadata('DC', 'title')
        if title_meta and title_meta[0][0]:
            # We still trust filename_title if it exists to avoid omnibus collision, 
            # but EPUB meta is generally better than PDF
            pass
            
        creator_meta = book.get_metadata('DC', 'creator')
        if creator_meta and creator_meta[0][0]:
            author = creator_meta[0][0]
            
        raw_text = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                raw_text.append(soup.get_text())
                
        return {
            "title": title,
            "author": author,
            "raw_text": "\n".join(raw_text)
        }

    def _extract_txt(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
            
        return {
            "title": self._clean_title(path.stem),
            "author": "Unknown",
            "raw_text": raw_text
        }
