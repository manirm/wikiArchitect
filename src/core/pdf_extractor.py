import os
from typing import Optional
from pypdf import PdfReader

class PDFExtractor:
    """Handles text extraction from PDF files for ingestion."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extracts all textual content from a PDF file.
        Returns an empty string if extraction fails or the file is invalid.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        try:
            reader = PdfReader(file_path)
            full_text = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            return "\n\n".join(full_text)
        except Exception as e:
            # In a production app, we would log this more specifically.
            print(f"[Error] Failed to extract PDF content: {str(e)}")
            return ""

    @staticmethod
    def get_metadata(file_path: str) -> dict:
        """
        Extracts basic metadata from the PDF (Author, Title, etc.)
        """
        try:
            reader = PdfReader(file_path)
            meta = reader.metadata
            return {
                "title": meta.get('/Title', os.path.basename(file_path)),
                "author": meta.get('/Author', 'Unknown'),
                "subject": meta.get('/Subject', ''),
                "creator": meta.get('/Creator', ''),
                "producer": meta.get('/Producer', ''),
                "num_pages": len(reader.pages)
            }
        except:
            return {}
