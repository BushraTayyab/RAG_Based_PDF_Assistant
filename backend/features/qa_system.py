from typing import List
from core.retriever import Retriever
from core.generator import AnswerGenerator
from models.schemas import QAResponse, Source

class QASystem:
    def __init__(self, retriever: Retriever, generator: AnswerGenerator):
        self.retriever = retriever
        self.generator = generator
    
    async def answer_question(self, query: str, collection_name: str, top_k: int = 5) -> QAResponse:
        print(f"🤔 Answering: {query}")
        
        retrieved_chunks = await self.retriever.retrieve(query, collection_name, top_k)
        print(f"📚 Retrieved {len(retrieved_chunks)} chunks")
        
        if not retrieved_chunks:
            return QAResponse(
                answer="No relevant information found in the document. Please try a different question.",
                sources=[],
                confidence_score=0.0
            )
        
        generation_result = self.generator.generate_answer(query, retrieved_chunks)
        
        sources = [
            Source(
                document_name=chunk.get('metadata', {}).get('filename', 'Unknown'),
                chunk_text=chunk.get('text', '')[:300],
                similarity_score=chunk.get('similarity_score', 0.5),
                chunk_index=i
            )
            for i, chunk in enumerate(retrieved_chunks[:3])
        ]
        
        return QAResponse(
            answer=generation_result['answer'],
            sources=sources,
            confidence_score=generation_result.get('confidence', 0.5)
        )
    
    async def answer_across_documents(self, query: str, collection_names: List[str], top_k: int = 5) -> QAResponse:
        all_chunks = []
        for collection_name in collection_names:
            chunks = await self.retriever.retrieve(query, collection_name, top_k)
            all_chunks.extend(chunks)
        
        all_chunks.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        if not all_chunks:
            return QAResponse(
                answer="No relevant information found across documents.",
                sources=[],
                confidence_score=0.0
            )
        
        generation_result = self.generator.generate_answer(query, all_chunks[:5])
        
        sources = [
            Source(
                document_name=chunk.get('metadata', {}).get('filename', 'Unknown'),
                chunk_text=chunk.get('text', '')[:300],
                similarity_score=chunk.get('similarity_score', 0.5),
                chunk_index=i
            )
            for i, chunk in enumerate(all_chunks[:3])
        ]
        
        return QAResponse(
            answer=generation_result['answer'],
            sources=sources,
            confidence_score=generation_result.get('confidence', 0.5)
        )