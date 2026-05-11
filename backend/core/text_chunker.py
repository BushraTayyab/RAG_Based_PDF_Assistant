from typing import List, Dict, Any

class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(self, text: str, doc_id: str, metadata: Dict = None) -> List[Dict]:
        if not text:
            return []
        
        if metadata is None:
            metadata = {}
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # Try to break at sentence
            if end < text_len:
                for i in range(min(end + 100, text_len) - 1, end, -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "doc_id": doc_id,
                    "chunk_index": len(chunks),
                    "text": chunk_text,
                    "metadata": metadata,
                    "chunk_length": len(chunk_text)
                })
            
            start = end - self.chunk_overlap if end < text_len else end
        
        return chunks