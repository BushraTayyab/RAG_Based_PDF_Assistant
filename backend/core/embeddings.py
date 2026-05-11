import numpy as np
from config import Config

class EmbeddingGenerator:
    def __init__(self):
        self.use_openai = Config.USE_OPENAI
        self.dimension = 384
        self.model = None
        
        print("Loading embedding model for document search...")
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384
            print("✅ Embedding model loaded! Documents will be searchable.")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
            self.model = None
    
    def generate_embeddings(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        if self.model is not None:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return np.array(embeddings)
        
        # Fallback
        return np.random.randn(len(texts), self.dimension)
    
    def embed_query(self, query):
        return self.generate_embeddings(query)