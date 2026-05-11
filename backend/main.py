from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import hashlib
from datetime import datetime

from config import Config
from core.document_processor import DocumentProcessor
from core.text_chunker import TextChunker
from core.embeddings import EmbeddingGenerator
from core.vector_store import VectorStore
from core.generator import AnswerGenerator
from core.retriever import Retriever
from features.qa_system import QASystem
from features.summarizer import DocumentSummarizer
from features.quiz_generator import QuizGenerator
from models.schemas import (
    QueryRequest, QAResponse, SummaryRequest, SummaryResponse,
    QuizRequest, QuizResponse, DocumentInfo, Source
)

app = FastAPI(title="Document QA RAG System", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
print("=" * 60)
print("🚀 Initializing Document QA RAG System...")
print("=" * 60)

doc_processor = DocumentProcessor()
text_chunker = TextChunker(chunk_size=Config.CHUNK_SIZE, chunk_overlap=Config.CHUNK_OVERLAP)
embedding_gen = EmbeddingGenerator()
vector_store = VectorStore()
retriever = Retriever(vector_store, embedding_gen)
answer_gen = AnswerGenerator()
qa_system = QASystem(retriever, answer_gen)
summarizer = DocumentSummarizer(vector_store, embedding_gen)
quiz_gen = QuizGenerator(vector_store, embedding_gen)

# Store active collections AND original text
active_collections = {}
document_texts = {}  # NEW: Store original document text

print("✅ System ready!")
print("=" * 60)

@app.get("/")
async def root():
    return {"message": "Document QA RAG System API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "collections": len(active_collections),
        "documents": len(active_collections),
        "openai_enabled": Config.USE_OPENAI and bool(Config.OPENAI_API_KEY)
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        print(f"\n📄 Uploading: {file.filename}")
        
        # Read file content
        content = await file.read()
        print(f"📏 Size: {len(content)} bytes")
        
        # Process document
        doc_data = await doc_processor.process_uploaded_file(file, content)
        print(f"✅ Document processed: {doc_data['doc_id']}")
        
        # STORE ORIGINAL TEXT (NEW)
        document_texts[doc_data['doc_id']] = doc_data['text']
        print(f"💾 Stored original text ({len(doc_data['text'])} chars)")
        
        # Create chunks
        chunks = text_chunker.chunk_document(
            doc_data['text'], 
            doc_data['doc_id'],
            metadata={"filename": doc_data['filename']}
        )
        print(f"📑 Created {len(chunks)} chunks")
        
        # Generate embeddings
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_gen.generate_embeddings(chunk_texts)
        print(f"🔢 Generated embeddings shape: {embeddings.shape}")
        
        # Store in vector database
        collection_name = f"doc_{doc_data['doc_id']}"
        vector_store.add_documents(collection_name, chunks, embeddings)
        
        active_collections[doc_data['doc_id']] = {
            "collection": collection_name,
            "filename": doc_data['filename'],
            "chunk_count": len(chunks),
            "upload_date": doc_data['upload_date']
        }
        
        print(f"💾 Stored in collection: {collection_name}")
        print(f"✅ Upload complete!\n")
        
        return DocumentInfo(
            id=doc_data['doc_id'],
            filename=doc_data['filename'],
            upload_date=doc_data['upload_date'],
            chunk_count=len(chunks),
            status="processed"
        )
    
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QAResponse)
async def ask_question(request: QueryRequest):
    """Ask a question about uploaded documents"""
    if not active_collections:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a document first.")
    
    print(f"\n🤔 Question: {request.query}")
    
    # Get the most recent document
    doc_id = list(active_collections.keys())[-1]
    collection_name = active_collections[doc_id]['collection']
    
    response = await qa_system.answer_question(
        query=request.query,
        collection_name=collection_name,
        top_k=request.top_k
    )
    
    print(f"✅ Answer generated (confidence: {response.confidence_score})\n")
    return response

@app.post("/query/all")
async def ask_all_documents(request: QueryRequest):
    """Ask a question across all uploaded documents"""
    if not active_collections:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a document first.")
    
    print(f"\n🤔 Question (all docs): {request.query}")
    
    collection_names = [info['collection'] for info in active_collections.values()]
    
    response = await qa_system.answer_across_documents(
        query=request.query,
        collection_names=collection_names,
        top_k=request.top_k
    )
    
    print(f"✅ Answer generated from {len(collection_names)} documents\n")
    return response

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_document(request: SummaryRequest = None):
    """Generate a summary of a document using its original text"""
    if not active_collections:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a document first.")
    
    if request is None:
        request = SummaryRequest()
    
    print(f"\n📝 Generating {request.style} summary...")
    
    # Get the most recent document
    doc_id = list(active_collections.keys())[-1]
    collection_name = active_collections[doc_id]['collection']
    
    # Get the original document text
    original_text = document_texts.get(doc_id, "")
    
    if not original_text:
        # Fallback: try to get from vector store
        print("⚠️ Original text not found, trying vector store...")
        result = await summarizer.summarize_document(
            collection_name=collection_name,
            style=request.style,
            max_length=request.max_length
        )
    else:
        print(f"📄 Using original document text ({len(original_text)} chars)")
        
        # Generate summary directly from original text
        if Config.USE_OPENAI and Config.OPENAI_API_KEY and len(original_text) > 100:
            import openai
            openai.api_key = Config.OPENAI_API_KEY
            
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a document summarization expert. Summarize the document content accurately."},
                        {"role": "user", "content": f"Please summarize this document:\n\n{original_text[:3500]}\n\nSummary:"}
                    ],
                    temperature=0.3,
                    max_tokens=400
                )
                summary = response.choices[0].message.content
                
                # Extract key points
                response2 = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Extract 5 key points from the document."},
                        {"role": "user", "content": f"Extract 5 key points from:\n\n{original_text[:3000]}\n\nKey points (one per line):"}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                key_points_text = response2.choices[0].message.content
                key_points = [p.strip("- • 1234567890. ").strip() for p in key_points_text.split('\n') if p.strip()][:5]
                
                print(f"✅ Summary generated via OpenAI")
                
                return SummaryResponse(
                    summary=summary,
                    key_points=key_points,
                    document_name=active_collections[doc_id]['filename']
                )
            except Exception as e:
                print(f"⚠️ OpenAI error: {e}")
                # Fallback to simple summary
                summary = original_text[:500] + "..." if len(original_text) > 500 else original_text
                sentences = [s.strip() for s in original_text.replace('\n', ' ').split('. ') if len(s.strip()) > 30]
                key_points = sentences[:5]
                
                return SummaryResponse(
                    summary=summary,
                    key_points=key_points,
                    document_name=active_collections[doc_id]['filename']
                )
        else:
            # Simple summary without OpenAI
            summary = original_text[:500] + "..." if len(original_text) > 500 else original_text
            sentences = [s.strip() for s in original_text.replace('\n', ' ').split('. ') if len(s.strip()) > 30]
            key_points = sentences[:5]
            
            return SummaryResponse(
                summary=summary,
                key_points=key_points,
                document_name=active_collections[doc_id]['filename']
            )
    
    return SummaryResponse(
        summary=result.get('summary', 'No summary available'),
        key_points=result.get('key_points', []),
        document_name=result.get('document_name', collection_name)
    )

@app.post("/quiz", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest = None):
    """Generate a quiz from document content"""
    if not active_collections:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a document first.")
    
    if request is None:
        request = QuizRequest()
    
    print(f"\n🎯 Generating quiz with {request.num_questions} questions (difficulty: {request.difficulty})...")
    
    # Get the most recent document
    doc_id = list(active_collections.keys())[-1]
    collection_name = active_collections[doc_id]['collection']
    
    # Get original text for better quiz generation
    original_text = document_texts.get(doc_id, "")
    
    if original_text and Config.USE_OPENAI and Config.OPENAI_API_KEY:
        import openai
        openai.api_key = Config.OPENAI_API_KEY
        
        try:
            prompt = f"""Generate {request.num_questions} {request.difficulty} multiple choice questions based on this document:

Document: {original_text[:2500]}

Return JSON array with questions. Each question must have:
- "question": the question text
- "question_type": "multiple_choice"
- "options": array of 4 options
- "correct_answer": the correct option
- "explanation": brief explanation

Example: [{{"question": "What is X?", "question_type": "multiple_choice", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "The document states..."}}]

Generate {request.num_questions} questions now:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a quiz generator. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            import json
            import re
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                return QuizResponse(
                    questions=questions[:request.num_questions],
                    metadata={"num_questions": len(questions), "difficulty": request.difficulty, "document": active_collections[doc_id]['filename']}
                )
        except Exception as e:
            print(f"Quiz generation error: {e}")
    
    # Fallback to simple quiz
    result = await quiz_gen.generate_quiz(
        collection_name=collection_name,
        num_questions=request.num_questions,
        difficulty=request.difficulty,
        question_types=request.question_types
    )
    
    return QuizResponse(
        questions=result['questions'],
        metadata=result['metadata']
    )

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    return [
        {
            "id": doc_id,
            "filename": info['filename'],
            "chunk_count": info['chunk_count'],
            "upload_date": info['upload_date']
        }
        for doc_id, info in active_collections.items()
    ]

@app.get("/documents/{doc_id}/content")
async def get_document_content(doc_id: str):
    """Get the original content of a document"""
    if doc_id not in active_collections:
        raise HTTPException(status_code=404, detail="Document not found")
    
    original_text = document_texts.get(doc_id, "")
    return {
        "id": doc_id,
        "filename": active_collections[doc_id]['filename'],
        "content": original_text[:5000],  # First 5000 chars
        "length": len(original_text)
    }

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    if doc_id not in active_collections:
        raise HTTPException(status_code=404, detail="Document not found")
    
    collection_name = active_collections[doc_id]['collection']
    vector_store.delete_collection(collection_name)
    del active_collections[doc_id]
    if doc_id in document_texts:
        del document_texts[doc_id]
    
    print(f"🗑️ Deleted document: {doc_id}")
    return {"message": f"Document deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("🎯 Document QA RAG System")
    print("=" * 60)
    print(f"📡 Backend API: http://{Config.HOST}:{Config.PORT}")
    print(f"📚 API Docs: http://{Config.HOST}:{Config.PORT}/docs")
    print(f"🎨 Frontend: http://localhost:3000")
    print(f"🔧 OpenAI: {'Enabled' if Config.USE_OPENAI and Config.OPENAI_API_KEY else 'Disabled (using local mode)'}")
    print("=" * 60)
    print("\n✅ System ready! Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT,
        log_level="info"
    )