import io
from typing import Dict, Any, List
import pypdf

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts raw textual stream from real PDF bytes."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_pages.append(f"--- Page {i+1} ---\n{text}")
        return "\n\n".join(extracted_pages) if extracted_pages else "Empty document or scanned image."
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"
