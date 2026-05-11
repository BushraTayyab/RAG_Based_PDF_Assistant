import openai
from typing import List, Dict, Any
from config import Config

class AnswerGenerator:
    def __init__(self):
        self.use_openai = Config.USE_OPENAI and Config.OPENAI_API_KEY
        
        if self.use_openai:
            openai.api_key = Config.OPENAI_API_KEY
            self.model = Config.LLM_MODEL
            print(f"✅ OpenAI enabled! Using model: {self.model}")
        else:
            print("⚠️ OpenAI not configured. Using simple mode.")
    
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict[str, Any]:
        if not context_chunks:
            return {
                "answer": "No relevant information found in the document.",
                "confidence": 0.0
            }
        
        # Prepare context
        context = "\n\n---\n\n".join([
            f"Source {i+1}: {chunk['text'][:1000]}" 
            for i, chunk in enumerate(context_chunks[:3])
        ])
        
        if self.use_openai:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based ONLY on the provided document context. Be concise and accurate. If the answer isn't in the context, say so clearly."},
                        {"role": "user", "content": f"""Context from document:
{context}

Question: {query}

Answer based only on the context above:"""}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                answer = response.choices[0].message.content
                
                return {
                    "answer": answer,
                    "confidence": 0.9,
                    "model": self.model
                }
            except Exception as e:
                print(f"OpenAI error: {e}")
                return self._simple_answer(query, context_chunks)
        else:
            return self._simple_answer(query, context_chunks)
    
    def _simple_answer(self, query: str, context_chunks: List) -> Dict:
        context_text = context_chunks[0]['text'][:500]
        return {
            "answer": f"Based on the document:\n\n{context_text}\n\n(Add OpenAI API key to .env file for better answers!)",
            "confidence": 0.5
        }