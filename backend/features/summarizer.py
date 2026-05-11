from typing import Dict, List
import openai
from config import Config

class DocumentSummarizer:
    def __init__(self, vector_store, embedding_generator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.use_openai = Config.USE_OPENAI and Config.OPENAI_API_KEY
        print(f"✅ Summarizer initialized (OpenAI: {self.use_openai})")
    
    async def summarize_document(self, collection_name: str, style: str = "concise", max_length: int = 500) -> Dict:
        try:
            print(f"📝 Generating document summary for: {collection_name}")
            
            # Get ALL document text from the collection
            full_text = await self._get_all_document_text(collection_name)
            
            print(f"📄 Extracted {len(full_text)} characters from document")
            print(f"📄 First 200 chars: {full_text[:200]}...")
            
            if not full_text or len(full_text) < 50:
                return {
                    "summary": "The document content could not be extracted. Please make sure the document contains readable text.",
                    "key_points": ["Document uploaded but content unavailable", "Try uploading a different document", "Ensure document has text content"],
                    "document_name": collection_name
                }
            
            # Generate REAL summary of the document content
            if self.use_openai and len(full_text) > 100:
                summary = await self._openai_content_summary(full_text, style, max_length)
                key_points = await self._openai_content_key_points(full_text)
            else:
                summary = self._extract_content_summary(full_text, max_length)
                key_points = self._extract_content_key_points(full_text)
            
            return {
                "summary": summary,
                "key_points": key_points[:5],
                "document_name": collection_name,
                "original_length": len(full_text),
                "summary_length": len(summary)
            }
        except Exception as e:
            print(f"❌ Summarizer error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "summary": "Unable to generate summary. Please try asking specific questions about the document instead.",
                "key_points": ["Try: 'What is this document about?'", "Try: 'Summarize the main points'"],
                "document_name": collection_name
            }
    
    async def _get_all_document_text(self, collection_name: str) -> str:
        """Get ALL text from the document collection"""
        collection = self.vector_store.create_collection(collection_name)
        full_text = ""
        
        # Method 1: If using in-memory storage with documents list
        if hasattr(collection, 'documents') and isinstance(collection['documents'], list):
            for doc in collection['documents']:
                if isinstance(doc, dict) and 'text' in doc:
                    full_text += doc['text'] + " "
                elif isinstance(doc, str):
                    full_text += doc + " "
        
        # Method 2: If using ChromaDB with get method
        elif hasattr(collection, 'get'):
            try:
                result = collection.get()
                if result and 'documents' in result and result['documents']:
                    full_text = " ".join(result['documents'])
            except:
                pass
        
        # Method 3: Try query with empty string
        if not full_text:
            try:
                result = collection.query(query_texts=[""], n_results=50)
                if result and 'documents' in result and result['documents']:
                    full_text = " ".join(result['documents'][0])
            except:
                pass
        
        # Method 4: Check if collection has documents attribute directly
        if not full_text and hasattr(collection, 'documents'):
            docs = collection.documents
            if docs:
                full_text = " ".join(docs)
        
        # Clean up text
        full_text = ' '.join(full_text.split())
        return full_text
    
    async def _openai_content_summary(self, text: str, style: str, max_length: int) -> str:
        """Generate REAL summary of document content using OpenAI"""
        try:
            style_instructions = {
                "concise": "Provide a brief, focused summary of what this document is about in 2-3 sentences.",
                "detailed": "Provide a comprehensive summary covering all major topics and key details from the document.",
                "bullet_points": "Provide the summary as 3-5 bullet points highlighting the main topics."
            }
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a document summarization expert. Your task is to summarize the actual content of the document provided. Focus only on what the document says."},
                    {"role": "user", "content": f"""Here is a document. Please summarize what this document is about.

DOCUMENT CONTENT:
{text[:3500]}

INSTRUCTIONS: {style_instructions.get(style, style_instructions['concise'])}
Keep the summary under {max_length} characters.

SUMMARY OF THE DOCUMENT:"""}
                ],
                temperature=0.3,
                max_tokens=min(max_length, 600)
            )
            summary = response.choices[0].message.content.strip()
            print(f"✅ OpenAI generated summary: {summary[:100]}...")
            return summary
        except Exception as e:
            print(f"⚠️ OpenAI summary failed: {e}")
            return self._extract_content_summary(text, max_length)
    
    async def _openai_content_key_points(self, text: str) -> List[str]:
        """Extract REAL key points from document content using OpenAI"""
        try:
            if len(text) > 3500:
                text = text[:3500]
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the most important key points from the document. Focus on factual information, main ideas, and key claims."},
                    {"role": "user", "content": f"""Extract 5 key points from this document. Each point should be a complete sentence that captures an important idea.

DOCUMENT:
{text}

KEY POINTS (numbered 1-5):"""}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse numbered key points
            key_points = []
            for line in content.split('\n'):
                line = line.strip()
                # Check for numbered lines (1., 2., etc.)
                if line and len(line) > 10:
                    # Remove number prefix
                    if line[0].isdigit() and '.' in line[:3]:
                        point = line.split('.', 1)[1].strip()
                        if point:
                            key_points.append(point)
                    elif line.startswith('-') or line.startswith('•'):
                        key_points.append(line[1:].strip())
                    elif len(key_points) < 5 and len(line) > 20:
                        key_points.append(line)
            
            # Clean up
            key_points = [p for p in key_points if len(p) > 15][:5]
            
            if key_points:
                print(f"✅ OpenAI extracted {len(key_points)} key points")
                return key_points
            else:
                return self._extract_content_key_points(text)
        except Exception as e:
            print(f"⚠️ OpenAI key points failed: {e}")
            return self._extract_content_key_points(text)
    
    def _extract_content_summary(self, text: str, max_length: int) -> str:
        """Extract summary directly from document content (no AI)"""
        # Take first few sentences that contain important information
        sentences = [s.strip() for s in text.replace('\n', ' ').split('. ') if len(s.strip()) > 30]
        
        if not sentences:
            # If no long sentences, take first 200 chars
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Build summary from important-looking sentences
        important_sentences = []
        
        # First sentence often contains main topic
        if sentences:
            important_sentences.append(sentences[0])
        
        # Look for sentences with key indicators
        key_indicators = ['important', 'key', 'main', 'overview', 'summary', 'conclusion', 'therefore', 'thus']
        for sentence in sentences[1:8]:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                important_sentences.append(sentence)
                if len(important_sentences) >= 3:
                    break
        
        # If not enough, add more first sentences
        if len(important_sentences) < 3 and len(sentences) > 1:
            for sentence in sentences[1:4]:
                if sentence not in important_sentences:
                    important_sentences.append(sentence)
        
        summary = ". ".join(important_sentences)
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary + "." if not summary.endswith('.') else summary
    
    def _extract_content_key_points(self, text: str) -> List[str]:
        """Extract key points directly from document content (no AI)"""
        sentences = [s.strip() for s in text.replace('\n', ' ').split('. ') if len(s.strip()) > 40]
        
        key_points = []
        
        # Look for sentences that seem important
        key_phrases = ['important', 'key point', 'main', 'significant', 'notably', 'primarily', 'essential', 'critical']
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(phrase in sentence_lower for phrase in key_phrases):
                if len(sentence) < 200:
                    key_points.append(sentence)
                    if len(key_points) >= 5:
                        break
        
        # If not enough, take first few sentences
        if len(key_points) < 3 and sentences:
            for sentence in sentences[:5]:
                if sentence not in key_points and len(sentence) < 200:
                    key_points.append(sentence)
                    if len(key_points) >= 5:
                        break
        
        # If still not enough, take any sentences
        if len(key_points) < 3 and sentences:
            for sentence in sentences[:3]:
                if sentence not in key_points:
                    key_points.append(sentence[:150])
        
        return key_points[:5]