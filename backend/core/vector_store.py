import os
import numpy as np
from typing import List, Dict, Any
import pickle

class VectorStore:
    """Simple vector store using FAISS (no Visual Studio needed)"""
    
    def __init__(self):
        self.persist_directory = "./faiss_index"
        os.makedirs(self.persist_directory, exist_ok=True)
        self.collections = {}
        print("✅ VectorStore initialized (FAISS mode)")
    
    def create_collection(self, collection_name: str):
        if collection_name not in self.collections:
            self.collections[collection_name] = {
                "documents": [],
                "embeddings": [],
                "ids": []
            }
        return self.collections[collection_name]
    
    def add_documents(self, collection_name: str, chunks: List[Dict], embeddings: np.ndarray):
        collection = self.create_collection(collection_name)
        
        ids = [f"{chunk['doc_id']}_{chunk['chunk_index']}" for chunk in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [{"filename": chunk.get('metadata', {}).get('filename', 'unknown')} for chunk in chunks]
        
        for i, doc_id in enumerate(ids):
            collection["ids"].append(doc_id)
            collection["documents"].append({
                "id": doc_id,
                "text": documents[i],
                "metadata": metadatas[i],
                "embedding": embeddings[i]
            })
            collection["embeddings"].append(embeddings[i])
        
        print(f"✅ Added {len(ids)} documents to {collection_name}")
        return len(ids)
    
    def search(self, collection_name: str, query_embedding: np.ndarray, top_k: int = 5):
        if collection_name not in self.collections:
            return []
        
        collection = self.collections[collection_name]
        if not collection["embeddings"]:
            return []
        
        # Convert to numpy array
        embeddings = np.array(collection["embeddings"])
        
        # Ensure query_embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        
        # Normalize documents
        docs_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
        
        # Calculate cosine similarity (dot product)
        similarities = np.dot(docs_norm, query_norm.T).flatten()
        
        # Get top k indices
        top_k = min(top_k, len(similarities))
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Only return if similarity > 0.1
                doc = collection["documents"][idx]
                results.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "similarity_score": float(similarities[idx]),
                    "id": doc["id"]
                })
        
        return results
    
    def delete_collection(self, collection_name: str):
        if collection_name in self.collections:
            del self.collections[collection_name]
            print(f"🗑️ Deleted: {collection_name}")
    
    def get_collection_stats(self, collection_name: str):
        if collection_name in self.collections:
            return {
                "name": collection_name,
                "document_count": len(self.collections[collection_name]["documents"]),
                "exists": True
            }
        return {"name": collection_name, "document_count": 0, "exists": False}