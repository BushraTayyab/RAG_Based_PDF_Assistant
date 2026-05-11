from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size: int

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    include_sources: Optional[bool] = True

class Source(BaseModel):
    document_name: str
    chunk_text: str
    similarity_score: float
    chunk_index: int

class QAResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence_score: float

class SummaryRequest(BaseModel):
    max_length: Optional[int] = 500
    style: Optional[str] = "concise"  # concise, detailed, bullet_points

class SummaryResponse(BaseModel):
    summary: str
    key_points: List[str]
    document_name: str

class QuizRequest(BaseModel):
    num_questions: Optional[int] = 3
    difficulty: Optional[str] = "medium"  # easy, medium, hard
    question_types: Optional[List[str]] = ["multiple_choice", "true_false"]

class QuizQuestion(BaseModel):
    question: str
    question_type: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    source_document: str

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    metadata: Dict[str, Any]

class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_date: str
    chunk_count: int
    status: str