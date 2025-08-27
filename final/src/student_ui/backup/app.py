from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

from src.utils.config import load_config
from src.store.chroma_store import ChromaStore
from src.embeddings.text_embedder import TextEmbedder
from src.rag.llm_client import OpenRouterClient, RAGSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
cfg = load_config()

# Create FastAPI app
app = FastAPI(title="VTU Study Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.url}")
    return response

# Mount static files for /static (for legacy or direct access)
app.mount("/static", StaticFiles(directory="src/student_ui/static"), name="static")

# Serve root path
@app.get("/")
async def get_root():
    return FileResponse("src/student_ui/static/index.html")

# Serve /styles.css from static root
@app.get("/styles.css")
async def get_styles():
    return FileResponse("src/student_ui/static/styles.css")

# Serve /js/* from static/js
@app.get("/js/{filename}")
async def get_js(filename: str):
    return FileResponse(f"src/student_ui/static/js/{filename}")

# Initialize components
try:
    # Convert configuration to appropriate types
    if isinstance(cfg, dict):
        from types import SimpleNamespace
        cfg = SimpleNamespace(**cfg)
    
    text_embedder = TextEmbedder(cfg)
    vector_store = ChromaStore(cfg, text_embedder)
    llm_client = OpenRouterClient(cfg)
    rag_system = RAGSystem(cfg, llm_client, vector_store)
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    rag_system = None  # Allow the app to start even if RAG is not available

@app.post("/api/chat")
async def chat_message(
    request: Request,
    message: str = Form(...),
    chat_history: str = Form("[]"),
    include_images: bool = Form(True),
    semester: str = Form(None),
    subject: str = Form(None)
):
    try:
        logger.info(f"Received chat request: {message}")
        chat_history_list = json.loads(chat_history)

        # Get response from RAG system
        response, sources, images, chat_history = rag_system.get_response(
            message, chat_history_list, subject, semester
        )

        return JSONResponse({
            "success": True,
            "response": response,
            "sources": sources,
            "images": images,
            "chat_history": chat_history
        })
    except Exception as e:
        logger.exception(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdfs")
async def list_pdfs(semester: Optional[str] = None, subject: Optional[str] = None):
    try:
        pdf_dir = Path("data/raw")
        pdfs = []

        if semester:
            pdf_dir = pdf_dir / semester
            if subject:
                pdf_dir = pdf_dir / subject

        for item in pdf_dir.rglob("*.pdf"):
            pdfs.append({
                "file_path": str(item),
                "file_size": item.stat().st_size,
                "book_title": item.parent.name,
                "subject": item.parts[-2] if semester else None,
                "semester": item.parts[-3] if semester else None
            })

        return JSONResponse({"success": True, "pdfs": pdfs})
    except Exception as e:
        logger.exception(f"Error listing PDFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/semesters")
async def list_semesters():
    try:
        semesters = [d.name for d in Path("data/raw").iterdir() if d.is_dir()]
        return JSONResponse({"success": True, "semesters": semesters})
    except Exception as e:
        logger.exception(f"Error listing semesters: {e}")
        raise HTTPException(status_code=500, detail=str(e))
