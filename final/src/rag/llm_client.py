from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional
import httpx
import logging

from src.store.chroma_store import ChromaStore
from src.embeddings.text_embedder import TextEmbedder

logger = logging.getLogger(__name__)

# Subject aliasing to match folder/metadata variants
SUBJECT_ALIASES: Dict[str, list[str]] = {
    "machine learning": ["ml", "machine_learning", "machinelearning", "machine learning"],
    "deep learning": ["dl", "deep_learning", "deeplearning", "deep learning"],
    "cryptography": ["cryptography", "crypto", "information_security", "crytography"],
    "crytography": ["cryptography", "crypto", "information_security", "crytography"],  # Handle typo in database
}

def subject_aliases(subject: Optional[str]) -> list[str]:
    if not subject:
        return []
    s = subject.strip().lower()
    base = {s, s.replace(" ", "_"), s.replace(" ", "")}
    base.update(SUBJECT_ALIASES.get(s, []))
    return list({*base})


class OpenRouterClient:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3-haiku"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate a response using OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", # Required by OpenRouter
                "X-Title": "Textbook RAG System" # Required by OpenRouter
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error: {str(e)}"


class RAGSystem:
    def __init__(self, llm_client: OpenRouterClient, store: ChromaStore, text_embedder: TextEmbedder):
        self.llm_client = llm_client
        self.store = store
        self.text_embedder = text_embedder
    
    def retrieve_relevant_chunks_universal(
        self, 
        query: str, 
        n_results: int = 10,
        modality: str = "text"
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from ALL VTU materials (universal access)"""
        try:
            # Embed the query
            if modality == "image" and hasattr(self, "image_embedder") and self.image_embedder is not None:
                query_embedding = self.image_embedder.embed_text([query])
            else:
                query_embedding = self.text_embedder.embed([query])
            if not query_embedding:
                return []
            
            # Only filter by modality, no subject/semester restrictions
            where_filter = {"modality": modality} if modality else None
            
            # Query the vector store
            if modality == "image":
                results = self.store.query_image(
                    embedding=query_embedding[0],
                    n_results=n_results,
                    where=where_filter
                )
            else:
                results = self.store.query_text(
                    embedding=query_embedding[0],
                    n_results=n_results,
                    where=where_filter
                )
            
            if not results or not results.get("metadatas"):
                return []
            
            # Format results
            chunks = []
            metadatas = results["metadatas"]
            if isinstance(metadatas, list) and len(metadatas) > 0:
                # ChromaDB returns metadatas as [[...]] - double nested list
                if isinstance(metadatas[0], list):
                    metadatas = metadatas[0]  # Unnest the first level
                
                for i, metadata in enumerate(metadatas):
                    content = ""
                    if results.get("documents"):
                        documents = results["documents"]
                        if isinstance(documents, list) and len(documents) > 0:
                            if isinstance(documents[0], list):
                                documents = documents[0]  # Unnest the first level
                            if i < len(documents):
                                content = str(documents[i])
                    
                    chunk = {
                        "content": content,
                        "metadata": metadata if isinstance(metadata, dict) else {},
                        "distance": results["distances"][0][i] if results.get("distances") and isinstance(results["distances"][0], list) and i < len(results["distances"][0]) else 0.0
                    }
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
            return []

    def retrieve_relevant_chunks(
        self, 
        query: str, 
        n_results: int = 5,
        subject: Optional[str] = None,
        semester: Optional[str] = None,
        book_title: Optional[str] = None,
        modality: str = "text"
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from the vector store"""
        try:
            # Embed the query
            if modality == "image" and hasattr(self, "image_embedder") and self.image_embedder is not None:
                query_embedding = self.image_embedder.embed_text([query])
            else:
                query_embedding = self.text_embedder.embed([query])
            if not query_embedding:
                return []
            
            # Build filter (prefer $and/$or to allow aliases)
            where_filter: Dict[str, Any] | None = None
            conditions: list[Dict[str, Any]] = []
            if modality:
                conditions.append({"modality": modality})
            if semester:
                conditions.append({"semester": semester})
            if book_title:
                conditions.append({"book_title": book_title})
            if subject:
                aliases = subject_aliases(subject)
                if len(aliases) > 1:
                    or_conds = [{"subject": alias} for alias in aliases]
                    conditions.append({"$or": or_conds})
                else:
                    conditions.append({"subject": subject})
            
            # Only use $and if we have multiple conditions
            if len(conditions) > 1:
                where_filter = {"$and": conditions}
            elif len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = None
            

            # Query the appropriate collection
            if modality == "image":
                results = self.store.query_image(
                    query_embedding[0],
                    n_results=n_results,
                    where=where_filter
                )
            else:
                results = self.store.query_text(
                    query_embedding[0],
                    n_results=n_results,
                    where=where_filter
                )
            

            
            chunks = []
            if results.get("metadatas"):
                # Handle nested metadata structure from ChromaDB
                metadatas = results["metadatas"]
                if isinstance(metadatas, list) and len(metadatas) > 0:
                    # ChromaDB returns metadatas as [[{...}]] - double nested list
                    if isinstance(metadatas[0], list):
                        metadatas = metadatas[0]  # Unnest the first level
                
                
                # Image queries return only metadatas in our store; text returns documents too
                if modality == "image":
                    for i, meta in enumerate(metadatas):
                        metadata = meta if isinstance(meta, dict) else {}
                        content = "[image]"
                        chunks.append({
                            "content": content,
                            "metadata": metadata,
                            "distance": results["distances"][0][i] if results.get("distances") and isinstance(results["distances"][0], list) else 0
                        })
                else:
                    if results.get("documents"):
                        documents = results["documents"]
                        if isinstance(documents, list) and len(documents) > 0:
                            # ChromaDB returns documents as [[...]] - double nested list
                            if isinstance(documents[0], list):
                                documents = documents[0]  # Unnest the first level
                        
                        for i, doc in enumerate(documents):
                            raw_metadata = metadatas[i] if i < len(metadatas) else {}
                            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
                            
                            if isinstance(doc, list):
                                content = " ".join(str(item) for item in doc)
                            else:
                                content = str(doc)
                            
                            chunks.append({
                                "content": content,
                                "metadata": metadata,
                                "distance": results["distances"][0][i] if results.get("distances") and isinstance(results["distances"][0], list) else 0
                            })
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def generate_answer(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate an answer using the LLM"""
        try:
            if not context_chunks:
                return "I don't have enough information to answer this question. Please try rephrasing or ask about a different topic."
            
            # Prepare context
            context_text = "\n\n".join([
                f"Source: {chunk['metadata'].get('book_title', 'Unknown')} - Page {chunk['metadata'].get('page', 'Unknown')}\n{chunk['content']}"
                for chunk in context_chunks
            ])
            
            # Prepare messages
            messages = []
            
            # Add system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system", 
                    "content": """You are a helpful VTU study assistant. Answer questions based on the provided context from textbooks. 

IMPORTANT: Structure your responses clearly with proper formatting:

1. **Main Answer**: Provide a comprehensive explanation
2. **Key Points**: Use bullet points (•) for clarity
3. **Examples**: Include practical examples when relevant
4. **Applications**: Mention real-world applications if applicable

FORMATTING RULES:
- Use double line breaks between sections
- Use bullet points (•) for lists
- Use bold text (**text**) for emphasis
- Maintain clear paragraph spacing

If the context doesn't contain enough information, say so. Be concise but thorough."""
                })
            
            # Add context
            messages.append({
                "role": "system",
                "content": f"Use this context from textbooks to help answer: {context_text}"
            })
            
            # Add user query
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Generate response
            response = self.llm_client.generate_response(
                messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Sorry, I encountered an error while generating the answer: {str(e)}"
    
    def generate_universal_answer(
        self, 
        query: str, 
        n_results: int = 10,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate an answer using ALL VTU materials (universal access)"""
        try:
            # Retrieve chunks from all materials
            text_chunks = self.retrieve_relevant_chunks_universal(query, n_results=n_results//2, modality="text")
            image_chunks = self.retrieve_relevant_chunks_universal(query, n_results=n_results//2, modality="image")
            
            # Combine and sort by relevance
            all_chunks = text_chunks + image_chunks
            all_chunks.sort(key=lambda x: x.get("distance", 0))
            
            if not all_chunks:
                return {
                    "answer": "I don't have enough information to answer this question. Please try rephrasing or ask about a different topic.",
                    "sources": [],
                    "chunks_used": 0
                }
            
            # Prepare context with better formatting
            context_parts = []
            sources = []
            
            for chunk in all_chunks[:n_results]:
                metadata = chunk.get("metadata", {})
                content = chunk.get("content", "")
                
                # Format source information
                semester = metadata.get("semester", "Unknown")
                subject = metadata.get("subject", "Unknown")
                book_title = metadata.get("book_title", "Unknown")
                page = metadata.get("page", "Unknown")
                
                source_info = f"Semester {semester} - {subject} - {book_title} (Page {page})"
                sources.append({
                    "semester": semester,
                    "subject": subject,
                    "book_title": book_title,
                    "page": page,
                    "type": metadata.get("modality", "text")
                })
                
                # Format content
                if metadata.get("modality") == "image":
                    context_parts.append(f"[IMAGE from {source_info}]: {content}")
                else:
                    context_parts.append(f"[TEXT from {source_info}]: {content}")
            
            context_text = "\n\n".join(context_parts)
            
            # Prepare messages
            messages = []
            
            # Add system prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system", 
                    "content": """You are a comprehensive VTU study assistant with access to ALL VTU materials across all semesters and subjects. 

IMPORTANT: Structure your responses clearly with proper formatting:
- Use **bold** for important terms and concepts
- Use bullet points for lists
- Use numbered lists for step-by-step processes
- Use code blocks for code examples
- Use blockquotes for important notes
- Maintain clear paragraph spacing

When answering:
1. Provide comprehensive information from multiple sources when relevant
2. Mention which subjects/semesters the information comes from
3. If information spans multiple subjects, explain the connections
4. Be thorough but organized in your response

If the context doesn't contain enough information, say so. Be concise but thorough."""
                })
            
            # Add context
            messages.append({
                "role": "system",
                "content": f"Use this context from VTU textbooks across all semesters and subjects to help answer: {context_text}"
            })
            
            # Add user query
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Generate response
            response = self.llm_client.generate_response(
                messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            return {
                "answer": response,
                "sources": sources,
                "chunks_used": len(all_chunks[:n_results])
            }
            
        except Exception as e:
            logger.error(f"Error generating universal answer: {e}")
            return {
                "answer": f"Sorry, I encountered an error while generating the answer: {str(e)}",
                "sources": [],
                "chunks_used": 0
            }
    
    def ask_question(
        self, 
        query: str, 
        n_results: int = 5,
        subject: Optional[str] = None,
        semester: Optional[str] = None,
        book_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ask a question and get an answer with context"""
        try:
            # Retrieve relevant text chunks
            context_chunks = self.retrieve_relevant_chunks(
                query, 
                n_results=n_results,
                subject=subject,
                semester=semester,
                book_title=book_title
            )

            # Retrieve relevant image chunks as well
            image_chunks = self.retrieve_relevant_chunks(
                query,
                n_results=min(4, n_results),
                subject=subject,
                semester=semester,
                book_title=book_title,
                modality="image",
            )
            # Thin image payload to only needed metadata
            images_payload = []
            for ch in image_chunks:
                meta = ch.get("metadata", {}) or {}
                img_path = meta.get("image_path")
                if img_path:
                    images_payload.append({
                        "book_title": meta.get("book_title"),
                        "page": meta.get("page"),
                        "image_index": meta.get("image_index"),
                        "subject": meta.get("subject"),
                        "semester": meta.get("semester"),
                        "image_path": img_path,
                    })

            if not context_chunks:
                return {
                    "answer": "I don't have enough information to answer this question. Please try rephrasing or ask about a different topic.",
                    "context_chunks": [],
                    "images": images_payload,
                    "num_chunks_retrieved": 0
                }
            
            # Generate answer
            answer = self.generate_answer(query, context_chunks)

            def infer_book_title_from_path(p: Optional[str]) -> Optional[str]:
                if not p:
                    return None
                try:
                    norm = p.replace("\\", "/")
                    parts = norm.split("/")
                    # Expect .../<subject>/<semester>/<book_title>/...
                    for i in range(len(parts) - 1):
                        if parts[i] == "processed" and i + 3 < len(parts):
                            return parts[i + 3]
                        if parts[i] == "raw" and i + 3 < len(parts):
                            return parts[i + 3]
                    # Fallback to parent directory name
                    return os.path.basename(os.path.dirname(norm)) or None
                except Exception:
                    return None

            def to_image_url(image_path: Optional[str]) -> Optional[str]:
                if not image_path:
                    return None
                norm = image_path.replace("\\", "/")
                idx = norm.find("data/processed/")
                rel = norm[idx + len("data/processed/"):] if idx >= 0 else norm
                return f"/processed/{rel}"

            # Build consolidated sources (dedup by book_title + page + modality)
            seen_keys = set()
            sources = []
            for ch in context_chunks:
                meta = ch.get("metadata", {}) or {}
                bt = meta.get("book_title") or infer_book_title_from_path(meta.get("source_path"))
                key = (bt, meta.get("page"), "text")
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                sources.append({
                    "type": "text",
                    "book_title": bt,
                    "page": meta.get("page"),
                    "subject": meta.get("subject"),
                    "semester": meta.get("semester"),
                    "source_path": meta.get("source_path"),
                })
            for im in images_payload:
                bt = im.get("book_title") or infer_book_title_from_path(im.get("image_path"))
                key = (bt, im.get("page"), "image")
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                sources.append({
                    "type": "image",
                    "book_title": bt,
                    "page": im.get("page"),
                    "subject": im.get("subject"),
                    "semester": im.get("semester"),
                    "image_path": im.get("image_path"),
                    "image_url": to_image_url(im.get("image_path")),
                })
            
            return {
                "answer": answer,
                "context_chunks": context_chunks,
                "images": images_payload,
                "sources": sources,
                "num_chunks_retrieved": len(context_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "context_chunks": [],
                "images": [],
                "num_chunks_retrieved": 0
            }
