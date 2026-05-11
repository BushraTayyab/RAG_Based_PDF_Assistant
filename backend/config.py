import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    USE_OPENAI = os.getenv("USE_OPENAI", "False").lower() == "true"  # Set to False by default to avoid API errors
    
    # Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    # Vector Store
    VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chromadb")
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    
    # Chunking
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Retrieval
    TOP_K_RETRIEVAL = 5
    SIMILARITY_THRESHOLD = 0.7
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Directories
    UPLOAD_DIR = "uploads"
    DATA_DIR = "data"
    
    # Create directories
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)