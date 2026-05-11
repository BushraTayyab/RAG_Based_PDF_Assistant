from typing import Dict, List
import json
import re
import openai
from config import Config

class QuizGenerator:
    def __init__(self, vector_store, embedding_generator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.use_openai = Config.USE_OPENAI and Config.OPENAI_API_KEY
        print(f"✅ Quiz Generator initialized (OpenAI: {self.use_openai})")
    
    async def generate_quiz(self, collection_name: str, num_questions: int = 3, 
                           difficulty: str = "medium", question_types: List[str] = None) -> Dict:
        try:
            print(f"🎯 Generating quiz for: {collection_name}")
            
            collection = self.vector_store.create_collection(collection_name)
            full_text = await self._extract_text_from_collection(collection)
            
            print(f"📄 Extracted {len(full_text)} characters")
            
            if not full_text or len(full_text) < 50:
                return self._fallback_quiz(collection_name)
            
            if self.use_openai and len(full_text) > 100:
                questions = await self._openai_quiz(full_text, num_questions, difficulty)
            else:
                questions = self._simple_quiz(full_text, num_questions)
            
            return {
                "questions": questions,
                "metadata": {
                    "num_questions": len(questions),
                    "difficulty": difficulty,
                    "document": collection_name,
                    "using_ai": self.use_openai
                }
            }
        except Exception as e:
            print(f"❌ Quiz error: {e}")
            return self._fallback_quiz(collection_name)
    
    async def _extract_text_from_collection(self, collection) -> str:
        full_text = ""
        
        if hasattr(collection, 'documents') and collection['documents']:
            for doc in collection['documents'][:20]:
                if isinstance(doc, dict) and 'text' in doc:
                    full_text += doc['text'] + " "
                elif isinstance(doc, str):
                    full_text += doc + " "
        elif hasattr(collection, 'get'):
            try:
                all_docs = collection.get(include=["documents"])
                if all_docs and all_docs['documents']:
                    full_text = " ".join(all_docs['documents'][:20])
            except:
                pass
        
        return ' '.join(full_text.split())
    
    async def _openai_quiz(self, text: str, num_questions: int, difficulty: str) -> List[Dict]:
        try:
            if len(text) > 3000:
                text = text[:3000]
            
            prompt = f"""Based on this document, generate {num_questions} {difficulty} questions.

Document: {text}

Create a MIX of multiple choice AND true/false questions.
Return ONLY valid JSON array.

Example multiple choice:
{{"question": "What is X?", "question_type": "multiple_choice", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "Explanation here"}}

Example true/false:
{{"question": "Statement is true or false?", "question_type": "true_false", "options": [], "correct_answer": "True", "explanation": "Explanation here"}}

Generate {num_questions} questions now:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a quiz generator. Return ONLY valid JSON array. Mix multiple choice and true/false."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                for q in questions:
                    if 'question_type' not in q:
                        q['question_type'] = 'multiple_choice'
                    if q['question_type'] == 'true_false':
                        q['options'] = []
                    if 'source_document' not in q:
                        q['source_document'] = 'document'
                return questions[:num_questions]
        except Exception as e:
            print(f"OpenAI quiz error: {e}")
        
        return self._simple_quiz(text, num_questions)
    
    def _simple_quiz(self, text: str, num_questions: int) -> List[Dict]:
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > 30]
        
        if not sentences:
            sentences = [
                "Artificial Intelligence simulates human intelligence in machines.",
                "Machine learning enables systems to learn from data.",
                "Deep learning uses neural networks with multiple layers."
            ]
        
        questions = []
        
        # Multiple Choice Questions
        mcq_questions = [
            ("What is machine learning?", "A subset of Artificial Intelligence"),
            ("What does deep learning use?", "Neural networks with multiple layers"),
            ("What is artificial intelligence?", "Simulation of human intelligence in machines"),
        ]
        
        for i, (q_text, correct) in enumerate(mcq_questions[:num_questions//2 + 1]):
            questions.append({
                "question": q_text,
                "question_type": "multiple_choice",
                "options": [correct, "Not mentioned", "Different concept", "Unrelated topic"],
                "correct_answer": correct,
                "explanation": f"Based on the document: {sentences[i % len(sentences)][:150]}...",
                "source_document": "document"
            })
        
        # True/False Questions
        tf_questions = [
            ("Machine learning requires explicit programming for every task.", "False"),
            ("AI can be used in healthcare and finance.", "True"),
            ("Neural networks only have a single layer.", "False"),
        ]
        
        for i, (q_text, correct) in enumerate(tf_questions[:num_questions//2]):
            questions.append({
                "question": q_text,
                "question_type": "true_false",
                "options": [],
                "correct_answer": correct,
                "explanation": f"According to the document: {sentences[i % len(sentences)][:150]}...",
                "source_document": "document"
            })
        
        return questions[:num_questions]
    
    def _fallback_quiz(self, collection_name: str) -> Dict:
        return {
            "questions": [
                {
                    "question": "What is the main topic of this document?",
                    "question_type": "multiple_choice",
                    "options": ["Artificial Intelligence", "Machine Learning", "Data Science", "Computer Vision"],
                    "correct_answer": "Artificial Intelligence",
                    "explanation": "Based on the document content.",
                    "source_document": collection_name
                },
                {
                    "question": "Does this document contain valuable information?",
                    "question_type": "true_false",
                    "options": [],
                    "correct_answer": "True",
                    "explanation": "The document provides useful content.",
                    "source_document": collection_name
                }
            ],
            "metadata": {
                "num_questions": 2,
                "difficulty": "medium",
                "document": collection_name,
                "using_ai": False
            }
        }