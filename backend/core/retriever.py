from typing import List, Dict
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore

class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_gen: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_gen = embedding_gen
    
    async def retrieve(self, query: str, collection_name: str, top_k: int = 5) -> List[Dict]:
        print(f"🔍 Retrieving for query: {query[:50]}...")
        query_embedding = self.embedding_gen.embed_query(query)
        results = self.vector_store.search(collection_name, query_embedding, top_k)
        print(f"📚 Retrieved {len(results)} results")
        return results
    
    async def retrieve_from_multiple(self, query: str, collection_names: List[str], top_k: int = 5) -> List[Dict]:
        all_results = []
        query_embedding = self.embedding_gen.embed_query(query)
        
        for collection_name in collection_names:
            results = self.vector_store.search(collection_name, query_embedding, top_k)
            all_results.extend(results)
        
        all_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        return all_results[:top_k]