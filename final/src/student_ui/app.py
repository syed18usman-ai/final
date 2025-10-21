from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import json

from src.utils.config import load_config
from src.store.chroma_store import ChromaStore
from src.embeddings.text_embedder import TextEmbedder
from src.rag.llm_client import OpenRouterClient, RAGSystem
from src.embeddings.image_embedder import ImageEmbedder
from src.services.profile_service import ProfileService
from src.services.vtu_news_scraper import VTUNewsScraper
from src.models.user_profile import UserProfile, ProfileUpdate, NewsItem
from src.auth.routes import router as auth_router
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
cfg = load_config()

# Create FastAPI app
app = FastAPI(title="VTU Study Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

# Serve static assets with no-cache headers
static_dir = Path("src/student_ui/static")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve processed images (extracted from PDFs)
processed_root = Path(cfg.get("data_dirs", {}).get("processed", "data/processed"))
if processed_root.exists():
    app.mount("/processed", StaticFiles(directory=str(processed_root)), name="processed")

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))

# Serve auth page
@app.get("/auth.html", response_class=HTMLResponse)
async def serve_auth():
    auth_path = static_dir / "auth.html"
    if not auth_path.exists():
        raise HTTPException(status_code=404, detail="Auth page not found")
    return HTMLResponse(auth_path.read_text(encoding="utf-8"))

# Serve profile page
@app.get("/profile.html", response_class=HTMLResponse)
async def serve_profile():
    profile_path = static_dir / "profile.html"
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Profile page not found")
    return HTMLResponse(profile_path.read_text(encoding="utf-8"))

# Initialize components (RAG)
try:
    # Chroma path from config with fallback
    chroma_path = cfg.get("storage", {}).get("chroma_path", "data/chroma")
    text_embedder = TextEmbedder(cfg)
    image_model_name = cfg.get("models", {}).get("image", "sentence-transformers/clip-ViT-B-32")
    image_embedder = ImageEmbedder(image_model_name)
    chroma_store = ChromaStore(chroma_path)

    llm_cfg = cfg.get("llm", {}) if isinstance(cfg, dict) else {}
    api_key = llm_cfg.get("api_key") or llm_cfg.get("openrouter_api_key") or ""
    model = llm_cfg.get("model", "anthropic/claude-3-haiku")
    llm_client = OpenRouterClient(api_key=api_key, model=model)

    rag_system = RAGSystem(llm_client=llm_client, store=chroma_store, text_embedder=text_embedder)
    rag_system.image_embedder = image_embedder  # attach for image query encoding
    
    # Initialize profile service
    profile_service = ProfileService()
    
    # Initialize news scraper
    news_scraper = VTUNewsScraper()
    
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    rag_system = None
    profile_service = None
    news_scraper = None

# API Routes
@app.get("/api/semesters")
async def get_semesters():
    try:
        semesters = sorted([s for s in chroma_store.get_semesters() if s])
        return semesters
    except Exception as e:
        logger.error(f"Error fetching semesters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subjects/{semester}")
async def get_subjects(semester: str):
    try:
        subjects = sorted([s for s in chroma_store.get_subjects(semester) if s])
        return subjects
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helpers for subject alias resolution
SUBJECT_ALIASES: dict[str, list[str]] = {
    "machine learning": ["ml", "machine_learning", "machinelearning"],
    "deep learning": ["dl", "deep_learning", "deeplearning"],
    "cryptography": ["cryptography", "crypto", "information_security", "crytography"],
    "crytography": ["cryptography", "crypto", "information_security", "crytography"],  # Handle typo in database
}

def resolve_candidate_subject_dirs(base: Path, subject: str) -> list[Path]:
    subj_lower = (subject or "").lower()
    candidates = {subj_lower, subj_lower.replace(" ", "_"), subj_lower.replace(" ", "")}
    candidates.update(SUBJECT_ALIASES.get(subj_lower, []))

    dirs: list[Path] = []
    # Exact matches
    for cand in candidates:
        d = base / cand
        if d.exists() and d.is_dir():
            dirs.append(d)
    # Fuzzy contains
    if not dirs and base.exists():
        for d in base.iterdir():
            if d.is_dir() and any(c in d.name.lower() for c in candidates):
                dirs.append(d)
    return dirs


def find_pdf_dirs(semester: str, subject: str) -> list[Path]:
    root = Path("data/raw")
    found: list[Path] = []

    # Normalize and build semester candidates
    sem_raw = (semester or "").strip()
    sem_lower = sem_raw.lower()
    sem_candidates = {
        sem_raw,  # original
        sem_lower,
        sem_lower.replace(" ", ""),
        f"sem{sem_lower}",
        f"semester{sem_lower}",
        f"sem_{sem_lower}",
        f"semester_{sem_lower}",
    }

    # Resolve candidate subject directories at root
    subj_dirs = resolve_candidate_subject_dirs(root, subject)

    # Pattern A: data/raw/<semester_variant>/<subject>/... (NEW PREFERRED STRUCTURE)
    for sem_cand in sem_candidates:
        base_sem = root / sem_cand
        if base_sem.exists():
            found.extend(resolve_candidate_subject_dirs(base_sem, subject))

    # Pattern B: data/raw/<subject>/<semester_variant>/... (LEGACY STRUCTURE - for backward compatibility)
    for sdir in subj_dirs:
        for sem_cand in sem_candidates:
            d = sdir / sem_cand
            if d.exists() and d.is_dir():
                found.append(d)

    # Fallbacks: subject root itself if specific semester not found
    if not found:
        found.extend([d for d in subj_dirs if d.exists() and d.is_dir()])

    # Last resort: entire root
    if not found and root.exists():
        found.append(root)
    return found


@app.get("/api/pdfs/{semester}/{subject}")
async def get_pdfs_fs(semester: str, subject: str):
    try:
        pdfs: list[dict[str, Any]] = []
        dirs = find_pdf_dirs(semester, subject)
        logger.info(f"PDF scan for semester={semester} subject={subject} dirs={[str(d) for d in dirs]}")
        seen = set()
        for dir_path in dirs:
            try:
                matches = list(dir_path.rglob("*.pdf"))
                logger.info(f"Scanning {dir_path} -> {len(matches)} pdf(s)")
                for pdf_path in matches:
                    key = str(pdf_path)
                    if key in seen:
                        continue
                    seen.add(key)
                    pdfs.append({
                        "book_title": pdf_path.parent.name,
                        "filename": pdf_path.name,
                        "file_path": str(pdf_path)
                    })
            except Exception as inner_e:
                logger.warning(f"Failed scanning {dir_path}: {inner_e}")
        logger.info(f"PDFs found: {len(pdfs)} for semester={semester} subject={subject}")
        return {"pdfs": pdfs}
    except Exception as e:
        logger.error(f"Error fetching PDFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def resolve_pdf_path(semester: str, subject: str, book_title: str, filename: str) -> Path | None:
    # Try both orders using the same directory resolution as listing
    for dir_path in find_pdf_dirs(semester, subject):
        candidate = dir_path / book_title / filename
        if candidate.exists():
            return candidate
    # Last resort: search within data/raw for filename under book_title
    root = Path("data/raw")
    for pdf_path in root.rglob(filename):
        if pdf_path.parent.name.lower() == book_title.lower():
            return pdf_path
    return None


@app.get("/api/pdfs/{semester}/{subject}/{book_title}/{filename}")
async def download_pdf_fs(semester: str, subject: str, book_title: str, filename: str):
    try:
        resolved = resolve_pdf_path(semester, subject, book_title, filename)
        if not resolved:
            raise HTTPException(status_code=404, detail="PDF not found")
        return FileResponse(str(resolved), media_type="application/pdf", filename=filename)
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint - JSON contract expected by frontend
@app.post("/api/chat")
async def chat(request: Request):
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG not initialized")
    try:
        data = await request.json()
        question = data.get("question") or data.get("message")
        include_images = bool(data.get("include_images", True))
        semester = data.get("semester")
        subject = data.get("subject")
        use_universal = data.get("use_universal", True)  # Default to universal access
        if not question:
            raise HTTPException(status_code=400, detail="question is required")

        logger.info(f"Chat request: question='{question}', semester='{semester}', subject='{subject}', universal={use_universal}")
        
        if use_universal:
            # Use universal RAG system - access all VTU materials
            result = rag_system.generate_universal_answer(
                query=question,
                n_results=10
            )
            # Convert to expected format
            formatted_result = {
                "answer": result["answer"],
                "sources": result["sources"],
                "num_chunks_retrieved": result["chunks_used"]
            }
        else:
            # Use subject-specific RAG system
            result = rag_system.ask_question(
                query=question,
                n_results=5,
                subject=subject,
                semester=semester
            )
            formatted_result = result
        
        logger.info(f"RAG result: answer_length={len(formatted_result.get('answer', ''))}, chunks={formatted_result.get('num_chunks_retrieved', 0)}, sources={len(formatted_result.get('sources', []))}")
        logger.info(f"Sources: {formatted_result.get('sources', [])}")
        
        return formatted_result
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Management Endpoints
@app.post("/api/profile")
async def create_profile(profile_data: dict):
    """Create a new user profile"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        user_id = profile_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        profile = profile_service.create_profile(user_id, profile_data)
        return {"message": "Profile created successfully", "profile": profile.dict()}
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile by ID"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        profile = profile_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile.dict()
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profile/{user_id}")
async def update_profile(user_id: str, update_data: ProfileUpdate):
    """Update user profile"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        profile = profile_service.update_profile(user_id, update_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"message": "Profile updated successfully", "profile": profile.dict()}
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# News Endpoints
@app.get("/api/news")
async def get_news(limit: int = 20):
    """Get all news items"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        news_items = profile_service.get_all_news(limit)
        return [item.dict() for item in news_items]
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/profile/{user_id}")
async def get_news_for_profile(user_id: str, limit: int = 10):
    """Get news relevant to user's profile"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        news_items = profile_service.get_news_for_profile(user_id, limit)
        return [item.dict() for item in news_items]
    except Exception as e:
        logger.error(f"Error getting profile news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/category/{category}")
async def get_news_by_category(category: str, limit: int = 10):
    """Get news by category"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        news_items = profile_service.get_news_by_category(category, limit)
        return [item.dict() for item in news_items]
    except Exception as e:
        logger.error(f"Error getting news by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/search")
async def search_news(query: str, limit: int = 10):
    """Search news by query"""
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    
    try:
        news_items = profile_service.search_news(query, limit)
        return [item.dict() for item in news_items]
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/news/refresh", methods=["GET", "POST"])
async def refresh_news():
    """Refresh news from VTU website"""
    if not news_scraper or not profile_service:
        raise HTTPException(status_code=500, detail="News service not available")
    try:
        # Scrape news from VTU website
        news_items = news_scraper.scrape_news()
        # Coerce and add
        profile_service.add_news_items(news_items)
        # Respond
        return {"message": f"Refreshed {len(news_items)} news items", "count": len(news_items)}
    except Exception as e:
        logger.error(f"Error refreshing news: {e}")
        # Return mock data if scraping fails
        from src.services.vtu_news_scraper import MOCK_NEWS_DATA
        profile_service.add_news_items(MOCK_NEWS_DATA)
        return {"message": "Using mock news data", "count": len(MOCK_NEWS_DATA)}

@app.get("/api/news/top-notifications")
async def get_top_notifications(limit: int = 10):
    if not profile_service:
        raise HTTPException(status_code=500, detail="Profile service not available")
    try:
        items = profile_service.get_top_notifications(limit)
        return [item.dict() for item in items]
    except Exception as e:
        logger.error(f"Error getting top notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))
