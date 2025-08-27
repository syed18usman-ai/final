from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from pathlib import Path
import shutil

from src.utils.config import load_config
from src.utils.logging import get_logger, ensure_dirs
from src.pipeline.ingest import IngestItem, run_ingest
from src.store.chroma_store import ChromaStore
from src.embeddings.text_embedder import TextEmbedder
from src.embeddings.image_embedder import ImageEmbedder
from src.rag.llm_client import OpenRouterClient, RAGSystem
from fastapi import UploadFile


cfg = load_config()
logger = get_logger(__name__)
app = FastAPI(title="Admin Panel")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="src/admin/static"), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


def verify_token(token: str = Form(...)):
    if token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True


class DeleteFilters(BaseModel):
    token: str
    subject: Optional[str] = None
    semester: Optional[str] = None
    book_title: Optional[str] = None
    source_path: Optional[str] = None
    modality: Optional[str] = None
    delete_source_files: Optional[bool] = False


class ListFilters(BaseModel):
    token: str
    subject: Optional[str] = None
    semester: Optional[str] = None
    book_title: Optional[str] = None
    source_path: Optional[str] = None
    modality: Optional[str] = None
    limit: int = 50


@app.post("/upload")
async def upload(
    subject: str = Form(...),
    semester: str = Form(...),
    book_title: str = Form(...),
    file: UploadFile = File(...),
    token: str = Form(...),
    token_ok: bool = Depends(verify_token),
):
    raw_dir = Path(cfg["data_dirs"]["raw"]) / subject / semester / book_title
    ensure_dirs(str(raw_dir))
    dest = raw_dir / file.filename
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    item = IngestItem(subject=subject, semester=semester, book_title=book_title, source_path=str(dest))
    run_ingest([item])
    return {"status": "ok", "stored": str(dest)}


@app.post("/delete")
async def delete(filters: DeleteFilters):
    if filters.token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    store = ChromaStore(cfg["storage"]["chroma_path"])
    where: Dict[str, Any] = {}
    for key in ["subject", "semester", "book_title", "source_path"]:
        val = getattr(filters, key)
        if val:
            where[key] = val
    if filters.modality:
        where["modality"] = filters.modality
    store.delete_text(where=where or None)
    store.delete_image(where=where or None)
    # Optionally delete source files from disk
    deleted_files: List[str] = []
    if filters.delete_source_files:
        import os
        # Gather unique source paths from remaining filters to safely remove
        res = store.list_text(where=where or None, limit=1000)
        metadatas = res.get("metadatas", []) or []
        paths = sorted({m.get("source_path") for m in metadatas if m.get("source_path")})
        for p in paths:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
                    deleted_files.append(p)
            except Exception:
                pass
    return {"status": "ok", "deleted_where": where, "deleted_files": deleted_files}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/items")
async def items(filters: ListFilters):
    if filters.token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    store = ChromaStore(cfg["storage"]["chroma_path"])
    where: Dict[str, Any] = {}
    for key in ["subject", "semester", "book_title", "source_path"]:
        val = getattr(filters, key)
        if val:
            where[key] = val
    if filters.modality == "image":
        res = store.list_image(where=where or None, limit=filters.limit)
    else:
        res = store.list_text(where=where or None, limit=filters.limit)
    # Do not return embeddings
    return JSONResponse(content=res)


@app.post("/search")
async def search(
    query: str = Form(...),
    token: str = Form(...),
    n_results: int = Form(5),
    modality: str = Form("text"),
    subject: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    book_title: Optional[str] = Form(None),
):
    if token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    store = ChromaStore(cfg["storage"]["chroma_path"])
    text_embedder = TextEmbedder(cfg["models"]["text"])
    
    # Create query embedding
    query_embedding = text_embedder.embed([query])[0]
    
    # Build where clause
    where: Dict[str, Any] = {}
    for key, val in [("subject", subject), ("semester", semester), ("book_title", book_title)]:
        if val:
            where[key] = val
    
    if modality == "image":
        # For images, we'll search text embeddings but return image results
        # This is a simplified approach - in practice you might want separate image search
        res = store.query_text(query_embedding, where=where or None, n_results=n_results)
    else:
        res = store.query_text(query_embedding, where=where or None, n_results=n_results)
    
    return JSONResponse(content=res)


@app.post("/stats")
async def get_stats(token: str = Form(...)):
    if token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    store = ChromaStore(cfg["storage"]["chroma_path"])
    
    text_count = store._text.count()
    image_count = store._image.count()
    total_chunks = text_count + image_count
    
    # Get recent uploads
    recent_uploads = []
    try:
        res = store.list_text(limit=100)
        metadatas = res.get("metadatas", []) or []
        for m in metadatas:
            if m.get("created_at"):
                recent_uploads.append({
                    "subject": m.get("subject", ""),
                    "semester": m.get("semester", ""),
                    "book_title": m.get("book_title", ""),
                    "created_at": m.get("created_at", ""),
                    "modality": m.get("modality", ""),
                    "page": m.get("page", -1)
                })
    except Exception:
        pass
    
    # Get subject breakdown
    subject_stats = {}
    try:
        res = store.list_text(limit=1000)
        metadatas = res.get("metadatas", []) or []
        for m in metadatas:
            subject = m.get("subject", "unknown")
            if subject not in subject_stats:
                subject_stats[subject] = {"text": 0, "image": 0}
            subject_stats[subject]["text"] += 1
        
        res = store.list_image(limit=1000)
        metadatas = res.get("metadatas", []) or []
        for m in metadatas:
            subject = m.get("subject", "unknown")
            if subject not in subject_stats:
                subject_stats[subject] = {"text": 0, "image": 0}
            subject_stats[subject]["image"] += 1
    except Exception:
        pass
    
    # Calculate storage sizes
    chroma_size = 0
    raw_size = 0
    processed_size = 0
    
    try:
        import os
        chroma_path = Path(cfg["storage"]["chroma_path"])
        if chroma_path.exists():
            for root, dirs, files in os.walk(chroma_path):
                for file in files:
                    chroma_size += os.path.getsize(os.path.join(root, file))
        
        raw_path = Path(cfg["data_dirs"]["raw"])
        if raw_path.exists():
            for root, dirs, files in os.walk(raw_path):
                for file in files:
                    raw_size += os.path.getsize(os.path.join(root, file))
        
        processed_path = Path(cfg["data_dirs"]["processed"])
        if processed_path.exists():
            for root, dirs, files in os.walk(processed_path):
                for file in files:
                    processed_size += os.path.getsize(os.path.join(root, file))
    except Exception:
        pass
    
    stats = {
        "overview": {
            "total_chunks": total_chunks,
            "text_chunks": text_count,
            "image_chunks": image_count,
            "total_subjects": len(subject_stats)
        },
        "storage": {
            "chroma_db_size_mb": round(chroma_size / (1024 * 1024), 2),
            "raw_files_size_mb": round(raw_size / (1024 * 1024), 2),
            "processed_files_size_mb": round(processed_size / (1024 * 1024), 2),
            "total_size_mb": round((chroma_size + raw_size + processed_size) / (1024 * 1024), 2)
        },
        "subjects": subject_stats,
        "recent_uploads": recent_uploads[:5]
    }
    
    return JSONResponse(content=stats)


@app.post("/health-check")
async def health_check(
    token: str = Form(...),
    subject: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    book_title: Optional[str] = Form(None),
):
    if token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    store = ChromaStore(cfg["storage"]["chroma_path"])
    
    # Build filter
    where: Dict[str, Any] = {}
    if subject:
        where["subject"] = subject
    if semester:
        where["semester"] = semester
    if book_title:
        where["book_title"] = book_title
    
    # Get text chunks
    text_health = {"total": 0, "avg_length": 0, "empty_chunks": 0, "sample_chunks": []}
    try:
        res = store.list_text(where=where or None, limit=1000)
        documents = res.get("documents", []) or []
        metadatas = res.get("metadatas", []) or []
        
        text_health["total"] = len(documents)
        if documents:
            lengths = [len(doc) for doc in documents if doc]
            text_health["avg_length"] = sum(lengths) / len(lengths) if lengths else 0
            text_health["empty_chunks"] = len([doc for doc in documents if not doc or not doc.strip()])
            text_health["sample_chunks"] = [doc[:200] + "..." if len(doc) > 200 else doc for doc in documents[:3]]
    except Exception as e:
        text_health["error"] = str(e)
    
    # Get image chunks
    image_health = {"total": 0, "by_page": {}, "sample_metadata": []}
    try:
        res = store.list_image(where=where or None, limit=1000)
        metadatas = res.get("metadatas", []) or []
        
        image_health["total"] = len(metadatas)
        if metadatas:
            # Group by page
            for meta in metadatas:
                page = meta.get("page", -1)
                if page not in image_health["by_page"]:
                    image_health["by_page"][page] = 0
                image_health["by_page"][page] += 1
            
            image_health["sample_metadata"] = metadatas[:3]
    except Exception as e:
        image_health["error"] = str(e)
    
    # Check source files
    file_health = {"missing_files": [], "file_sizes": {}}
    try:
        import os
        raw_path = Path(cfg["data_dirs"]["raw"])
        if raw_path.exists():
            for meta in metadatas:
                source_path = meta.get("source_path", "")
                if source_path:
                    file_path = Path(source_path)
                    if file_path.exists():
                        file_health["file_sizes"][source_path] = os.path.getsize(file_path)
                    else:
                        file_health["missing_files"].append(source_path)
    except Exception as e:
        file_health["error"] = str(e)
    
    # Quality metrics
    quality_metrics = {
        "text_quality": {
            "completeness": (text_health["total"] - text_health["empty_chunks"]) / max(text_health["total"], 1) * 100,
            "avg_chunk_length": text_health["avg_length"],
            "empty_chunk_ratio": text_health["empty_chunks"] / max(text_health["total"], 1) * 100
        },
        "image_quality": {
            "total_images": image_health["total"],
            "pages_with_images": len(image_health["by_page"]),
            "avg_images_per_page": image_health["total"] / max(len(image_health["by_page"]), 1)
        },
        "file_integrity": {
            "missing_files": len(file_health["missing_files"]),
            "total_files": len(file_health["file_sizes"])
        }
    }
    
    health_report = {
        "filter": where,
        "text_health": text_health,
        "image_health": image_health,
        "file_health": file_health,
        "quality_metrics": quality_metrics,
        "recommendations": []
    }
    
    # Generate recommendations
    if text_health["empty_chunks"] > 0:
        health_report["recommendations"].append(f"Found {text_health['empty_chunks']} empty text chunks - consider re-uploading")
    
    if text_health["avg_length"] < 50:
        health_report["recommendations"].append("Average text chunk length is very short - may indicate extraction issues")
    
    if image_health["total"] == 0 and text_health["total"] > 0:
        health_report["recommendations"].append("No images found but text exists - check if PDF contains images")
    
    if file_health["missing_files"]:
        health_report["recommendations"].append(f"Found {len(file_health['missing_files'])} missing source files")
    
    return JSONResponse(content=health_report)


@app.post("/ask")
async def ask_question(
    query: str = Form(...),
    token: str = Form(...),
    n_results: int = Form(5),
    subject: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    book_title: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
):
    if token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if LLM is configured
    if not cfg.get("llm", {}).get("api_key"):
        return JSONResponse(content={
            "error": "LLM not configured. Please set your OpenRouter API key in config.yaml"
        })
    
    try:
        # Initialize components
        store = ChromaStore(cfg["storage"]["chroma_path"])
        text_embedder = TextEmbedder(cfg["models"]["text"])
        
        # Initialize LLM client
        llm_client = OpenRouterClient(
            api_key=cfg["llm"]["api_key"],
            model=cfg["llm"]["model"]
        )
        
        # Initialize RAG system
        rag_system = RAGSystem(llm_client, store, text_embedder)
        
        # Ask question
        result = rag_system.ask_question(
            query=query,
            n_results=n_results,
            subject=subject,
            semester=semester,
            book_title=book_title,
            system_prompt=system_prompt or cfg["llm"].get("system_prompt")
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        return JSONResponse(content={
            "error": f"Failed to process question: {str(e)}",
            "query": query
        })


@app.post("/chat")
async def chat_conversation(
    messages: List[Dict[str, str]] = Form(...),
    token: str = Form(...),
    n_results: int = Form(5),
    subject: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    book_title: Optional[str] = Form(None),
):
    if token != cfg["admin"]["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if LLM is configured
    if not cfg.get("llm", {}).get("api_key"):
        return JSONResponse(content={
            "error": "LLM not configured. Please set your OpenRouter API key in config.yaml"
        })
    
    try:
        # Get the last user message
        if not messages or not isinstance(messages, list):
            return JSONResponse(content={"error": "Invalid messages format"})
        
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content")
                break
        
        if not last_user_message:
            return JSONResponse(content={"error": "No user message found"})
        
        # Initialize components
        store = ChromaStore(cfg["storage"]["chroma_path"])
        text_embedder = TextEmbedder(cfg["models"]["text"])
        
        # Initialize LLM client
        llm_client = OpenRouterClient(
            api_key=cfg["llm"]["api_key"],
            model=cfg["llm"]["model"]
        )
        
        # Initialize RAG system
        rag_system = RAGSystem(llm_client, store, text_embedder)
        
        # Get relevant chunks
        chunks = rag_system.retrieve_relevant_chunks(
            last_user_message,
            n_results=n_results,
            subject=subject,
            semester=semester,
            book_title=book_title
        )
        
        # Prepare context
        context_text = "\n\n".join([
            f"Source: {chunk['metadata'].get('book_title', 'Unknown')} - Page {chunk['metadata'].get('page', 'Unknown')}\n{chunk['content']}"
            for chunk in chunks
        ])
        
        # Prepare messages for LLM
        llm_messages = []
        
        # Add system message
        llm_messages.append({
            "role": "system",
            "content": cfg["llm"].get("system_prompt", "You are a helpful educational assistant.")
        })
        
        # Add context if available
        if context_text:
            llm_messages.append({
                "role": "system",
                "content": f"Use this context from textbooks to help answer: {context_text}"
            })
        
        # Add conversation history
        llm_messages.extend(messages)
        
        # Generate response
        response = llm_client.generate_response(
            llm_messages,
            max_tokens=cfg["llm"].get("max_tokens", 1000),
            temperature=cfg["llm"].get("temperature", 0.7)
        )
        
        return JSONResponse(content={
            "response": response,
            "context_chunks": chunks,
            "query": last_user_message
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return JSONResponse(content={
            "error": f"Failed to process chat: {str(e)}"
        })


@app.post("/upload-batch")
async def upload_batch(
    subject: str = Form(...),
    semester: str = Form(...),
    book_title: str = Form(...),
    files: List[UploadFile] = File(...),
    token: str = Form(...),
    token_ok: bool = Depends(verify_token),
):
    raw_dir = Path(cfg["data_dirs"]["raw"]) / subject / semester / book_title
    ensure_dirs(str(raw_dir))
    stored: List[str] = []
    for file in files:
        dest = raw_dir / file.filename
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        stored.append(str(dest))
    # Kick off ingest sequentially for now (simple)
    items = [IngestItem(subject=subject, semester=semester, book_title=book_title, source_path=p) for p in stored]
    run_ingest(items)
    return {"status": "ok", "stored": stored, "count": len(stored)}
