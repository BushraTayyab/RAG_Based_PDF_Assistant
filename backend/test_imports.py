print("Testing all imports...")

try:
    from fastapi import FastAPI
    print("✅ fastapi")
except Exception as e:
    print(f"❌ fastapi: {e}")

try:
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ CORS middleware")
except Exception as e:
    print(f"❌ CORS: {e}")

try:
    from fastapi.responses import JSONResponse
    print("✅ JSONResponse")
except Exception as e:
    print(f"❌ JSONResponse: {e}")

try:
    import dotenv
    print("✅ dotenv")
except Exception as e:
    print(f"❌ dotenv: {e}")

try:
    import fitz
    print("✅ PyMuPDF")
except Exception as e:
    print(f"❌ PyMuPDF: {e}")

try:
    from docx import Document
    print("✅ python-docx")
except Exception as e:
    print(f"❌ python-docx: {e}")

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers")
except Exception as e:
    print(f"❌ sentence-transformers: {e}")

try:
    import chromadb
    print("✅ chromadb")
except Exception as e:
    print(f"❌ chromadb: {e}")

try:
    import openai
    print("✅ openai")
except Exception as e:
    print(f"❌ openai: {e}")

try:
    import numpy as np
    print("✅ numpy")
except Exception as e:
    print(f"❌ numpy: {e}")

print("\n" + "="*40)
print("If all say ✅, you're ready to run the backend!")
print("If any say ❌, install that specific package")
print("="*40)