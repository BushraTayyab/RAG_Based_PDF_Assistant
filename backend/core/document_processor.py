import os
import hashlib
from datetime import datetime
from typing import Dict, Any

class DocumentProcessor:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✅ DocumentProcessor ready")
    
    async def process_uploaded_file(self, file, file_content: bytes) -> Dict[str, Any]:
        filename = file.filename
        ext = filename.split('.')[-1].lower()
        
        # Save temp file
        temp_path = os.path.join(self.upload_dir, filename)
        with open(temp_path, "wb") as f:
            f.write(file_content)
        
        # Extract text
        if ext == 'txt':
            text = self._read_txt(temp_path)
        elif ext == 'pdf':
            text = self._read_pdf(temp_path)
        elif ext == 'docx':
            text = self._read_docx(temp_path)
        else:
            text = f"Unsupported file type: {ext}"
        
        os.remove(temp_path)
        
        doc_id = hashlib.md5(f"{filename}_{datetime.now()}".encode()).hexdigest()
        
        return {
            "doc_id": doc_id,
            "filename": filename,
            "text": text,
            "length": len(text),
            "upload_date": datetime.now().isoformat()
        }
    
    def _read_txt(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _read_pdf(self, path: str) -> str:
        try:
            import fitz
            doc = fitz.open(path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except:
            return "PDF reading failed. Install PyMuPDF: pip install PyMuPDF"
    
    def _read_docx(self, path: str) -> str:
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            return "DOCX reading failed. Install python-docx: pip install python-docx"