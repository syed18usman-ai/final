from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.config import load_config
from src.utils.id_utils import file_sha1, stable_chunk_id
from src.utils.logging import get_logger, ensure_dirs
from src.extract.pdf_extractor import extract_text, extract_images
from src.chunking.text_chunker import split_text
from src.embeddings.text_embedder import TextEmbedder
from src.embeddings.image_embedder import ImageEmbedder
from src.store.chroma_store import ChromaStore
from src.utils.failures import append_failure


logger = get_logger(__name__)


@dataclass
class IngestItem:
    subject: str
    semester: str
    book_title: str
    source_path: str


def ingest_pdf(item: IngestItem, cfg: Dict[str, Any], store: ChromaStore, text_embedder: TextEmbedder, image_embedder: ImageEmbedder) -> None:
    path = Path(item.source_path)
    if not path.exists():
        logger.error("source file missing", extra={"extra": {"path": str(path)}})
        return

    logger.info(f"Starting PDF ingestion: {path}")
    source_hash = file_sha1(path)
    created_at = datetime.utcnow().isoformat()

    # text
    logger.info(f"Extracting text from PDF...")
    pages = extract_text(path)
    logger.info(f"Extracted text from {len(pages)} pages")
    
    text_chunks: List[str] = []
    text_metadatas: List[Dict[str, Any]] = []
    text_ids: List[str] = []
    for p in pages:
        chunks = split_text(p.text, cfg["chunking"]["max_chars"], cfg["chunking"]["overlap"])
        for idx, chunk in enumerate(chunks):
            meta = {
                "modality": "text",
                "subject": item.subject,
                "semester": item.semester,
                "book_title": item.book_title,
                "page": p.page_index,
                "chunk_index": idx,
                "source_path": str(path),
                "source_hash": source_hash,
                "created_at": created_at,
            }
            cid = stable_chunk_id(meta)
            text_ids.append(cid)
            text_chunks.append(chunk)
            text_metadatas.append(meta)

    if text_chunks:
        logger.info(f"Embedding {len(text_chunks)} text chunks...")
        text_embeddings = text_embedder.embed(text_chunks)
        store.upsert_text(text_ids, text_embeddings, text_chunks, text_metadatas)
        logger.info(f"Successfully stored {len(text_chunks)} text chunks")

    # images
    logger.info(f"Extracting images from PDF...")
    imgs = extract_images(path)
    logger.info(f"Extracted {len(imgs)} images from PDF")
    
    image_bytes = [im.image_bytes for im in imgs]
    image_ids: List[str] = []
    image_metadatas: List[Dict[str, Any]] = []
    # save images to processed dir
    processed_base = Path(cfg["data_dirs"]["processed"]) / item.semester / item.subject / item.book_title / "images"
    ensure_dirs(str(processed_base))
    for i, im in enumerate(imgs):
        meta = {
            "modality": "image",
            "subject": item.subject,
            "semester": item.semester,
            "book_title": item.book_title,
            "page": im.page_index,
            "image_index": im.image_index,
            "source_path": str(path),
            "source_hash": source_hash,
            "created_at": created_at,
            "image_ext": im.ext,
        }
        img_name = f"page_{im.page_index}_img_{im.image_index}.{im.ext}"
        img_path = processed_base / img_name
        try:
            with img_path.open("wb") as f:
                f.write(im.image_bytes)
            meta["image_path"] = str(img_path)
        except Exception as e:
            logger.exception("failed saving image", extra={"extra": {"path": str(img_path)}})
        cid = stable_chunk_id(meta)
        image_ids.append(cid)
        image_metadatas.append(meta)

    if image_bytes:
        logger.info(f"Embedding {len(image_bytes)} images (this may take a while)...")
        image_embeddings, valid_indices = image_embedder.embed_bytes(image_bytes)
        logger.info(f"Successfully embedded {len(image_embeddings)} images (skipped {len(image_bytes) - len(image_embeddings)})")
        # Filter arrays to match successful embeddings using valid_indices
        if valid_indices:
            filtered_image_ids = [image_ids[i] for i in valid_indices]
            filtered_image_metadatas = [image_metadatas[i] for i in valid_indices]
            store.upsert_image(filtered_image_ids, image_embeddings, filtered_image_metadatas)
            logger.info(f"Successfully stored {len(filtered_image_ids)} image embeddings")
    
    logger.info(f"PDF ingestion completed: {path}")


def ingest_image_file(item: IngestItem, cfg: Dict[str, Any], store: ChromaStore, image_embedder: ImageEmbedder) -> None:
    path = Path(item.source_path)
    if not path.exists():
        logger.error("source image missing", extra={"extra": {"path": str(path)}})
        return
    source_hash = file_sha1(path)
    created_at = datetime.utcnow().isoformat()
    # read bytes
    data = path.read_bytes()
    # save processed copy
    ext = path.suffix.lstrip(".") or "png"
    processed_base = Path(cfg["data_dirs"]["processed"]) / item.semester / item.subject / item.book_title / "images"
    ensure_dirs(str(processed_base))
    img_name = path.name
    dest_path = processed_base / img_name
    dest_path.write_bytes(data)
    meta = {
        "modality": "image",
        "subject": item.subject,
        "semester": item.semester,
        "book_title": item.book_title,
        "page": -1,
        "image_index": 0,
        "source_path": str(path),
        "source_hash": source_hash,
        "created_at": created_at,
        "image_ext": ext,
        "image_path": str(dest_path),
    }
    cid = stable_chunk_id(meta)
    emb, valid_indices = image_embedder.embed_bytes([data])
    if valid_indices:  # Only insert if embedding was successful
        store.upsert_image([cid], emb, [meta])


def run_ingest(items: List[IngestItem]) -> None:
    cfg = load_config()
    ensure_dirs(cfg["storage"]["chroma_path"], cfg["data_dirs"]["logs"])
    store = ChromaStore(cfg["storage"]["chroma_path"])
    text_embedder = TextEmbedder(cfg["models"]["text"])
    image_embedder = ImageEmbedder(cfg["models"]["image"])

    for item in items:
        try:
            # decide by extension
            if str(item.source_path).lower().endswith(".pdf"):
                ingest_pdf(item, cfg, store, text_embedder, image_embedder)
            else:
                ingest_image_file(item, cfg, store, image_embedder)
        except Exception as e:
            payload = {"subject": item.subject, "semester": item.semester, "book": item.book_title, "path": item.source_path, "error": str(e)}
            logger.exception("ingest failed", extra={"extra": payload})
            append_failure(cfg["data_dirs"]["logs"], "ingest_failed", payload)
