QA_SYSTEM_PROMPT = """You are an AI assistant that answers questions based strictly on the provided document context. Only use information from the context. If the answer cannot be found, say so clearly."""

QA_USER_PROMPT_TEMPLATE = """Context from documents:
{context}

Question: {query}

Answer based only on the context above:"""

SUMMARY_SYSTEM_PROMPT = "You are a document summarization expert. Create clear, accurate summaries."

SUMMARY_USER_TEMPLATE = """Please summarize the following document:

{document_text}

Style: {style}
Maximum length: {max_length} words"""

QUIZ_GENERATION_PROMPT = """Generate {num_questions} {difficulty} questions based on this document:

{text}

Return as JSON array."""