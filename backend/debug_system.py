import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from core.document_processor import DocumentProcessor
from core.text_chunker import TextChunker
from core.embeddings import EmbeddingGenerator
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.generator import AnswerGenerator
from features.qa_system import QASystem

print("=" * 60)
print("DEBUGGING DOCUMENT QA SYSTEM")
print("=" * 60)

# 1. Check config
print(f"\n1. Config:")
print(f"   USE_OPENAI: {Config.USE_OPENAI}")
print(f"   API Key set: {bool(Config.OPENAI_API_KEY)}")

# 2. Test document processing
print(f"\n2. Testing document processor...")
doc_processor = DocumentProcessor()

# Create a test document
test_text = """Artificial Intelligence is the simulation of human intelligence in machines.
Machine learning is a subset of AI that enables systems to learn from data.
Deep learning uses neural networks with multiple layers to process information.
Natural Language Processing helps computers understand human language.
Computer vision allows machines to see and interpret visual information.
AI applications include healthcare, finance, transportation, and education."""

print(f"   Test document length: {len(test_text)} chars")

# 3. Test chunking
print(f"\n3. Testing text chunker...")
text_chunker = TextChunker(chunk_size=500, chunk_overlap=50)
chunks = text_chunker.chunk_document(test_text, "test_doc", {"filename": "test.txt"})
print(f"   Created {len(chunks)} chunks")

for i, chunk in enumerate(chunks[:2]):
    print(f"   Chunk {i}: {chunk['text'][:100]}...")

# 4. Test embeddings
print(f"\n4. Testing embeddings...")
embedding_gen = EmbeddingGenerator()
chunk_texts = [chunk['text'] for chunk in chunks]
embeddings = embedding_gen.generate_embeddings(chunk_texts)
print(f"   Embeddings shape: {embeddings.shape}")

# 5. Test vector store
print(f"\n5. Testing vector store...")
vector_store = VectorStore()
collection_name = "test_collection"
vector_store.add_documents(collection_name, chunks, embeddings)
print(f"   Added to collection: {collection_name}")

# 6. Test retrieval
print(f"\n6. Testing retrieval...")
retriever = Retriever(vector_store, embedding_gen)
import asyncio

async def test_retrieval():
    query = "What is machine learning?"
    results = await retriever.retrieve(query, collection_name, top_k=3)
    print(f"   Query: '{query}'")
    print(f"   Retrieved {len(results)} results")
    for i, result in enumerate(results):
        print(f"   Result {i}: score={result.get('similarity_score', 0):.3f}")
        print(f"     Text: {result.get('text', '')[:150]}...")
    return results

results = asyncio.run(test_retrieval())

# 7. Test answer generation
print(f"\n7. Testing answer generation...")
generator = AnswerGenerator()
qa_system = QASystem(retriever, generator)

async def test_qa():
    response = await qa_system.answer_question("What is machine learning?", collection_name)
    print(f"   Answer: {response.answer}")
    print(f"   Confidence: {response.confidence_score}")
    return response

qa_response = asyncio.run(test_qa())

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)