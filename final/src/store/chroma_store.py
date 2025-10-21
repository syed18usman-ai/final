from __future__ import annotations

from typing import Any, Dict, List, Optional
import chromadb
from chromadb.utils import embedding_functions


class ChromaStore:
    def __init__(self, persist_directory: str) -> None:
        self.client = chromadb.PersistentClient(path=persist_directory)
        self._text = self.client.get_or_create_collection("text_chunks")
        self._image = self.client.get_or_create_collection("image_chunks")

    # helpers
    def _normalize_where(self, where: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not where:
            return None
        # Return as-is if it's already a complex query
        if any(op in where for op in ("$and", "$or", "$not")):
            return where
        # For simple queries, ChromaDB expects direct key-value pairs
        # or single operator format
        if len(where) == 1:
            # Single condition - use direct format
            key, value = next(iter(where.items()))
            if isinstance(value, dict) and "$eq" in value:
                return {key: value}
            else:
                return {key: value}
        else:
            # Multiple conditions - use $and
            conditions = []
            for k, v in where.items():
                if isinstance(v, dict) and "$eq" in v:
                    conditions.append({k: v})
                else:
                    conditions.append({k: v})
            return {"$and": conditions}

    # text
    def upsert_text(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        self._text.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def delete_text(self, where: Optional[Dict[str, Any]] = None, ids: Optional[List[str]] = None):
        self._text.delete(where=self._normalize_where(where), ids=ids)

    def query_text(self, embedding: List[float], where: Optional[Dict[str, Any]] = None, n_results: int = 5):
        return self._text.query(query_embeddings=[embedding], where=self._normalize_where(where), n_results=n_results)

    # image
    def upsert_image(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        self._image.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def delete_image(self, where: Optional[Dict[str, Any]] = None, ids: Optional[List[str]] = None):
        self._image.delete(where=self._normalize_where(where), ids=ids)

    def query_image(self, embedding: List[float], where: Optional[Dict[str, Any]] = None, n_results: int = 5):
        return self._image.query(query_embeddings=[embedding], where=self._normalize_where(where), n_results=n_results)

    def list_text(self, where: Optional[Dict[str, Any]] = None, limit: int = 50):
        # Chroma get() include cannot contain 'ids'; it is returned by default.
        return self._text.get(where=self._normalize_where(where), limit=limit, include=["metadatas", "documents"])

    def list_image(self, where: Optional[Dict[str, Any]] = None, limit: int = 50):
        return self._image.get(where=self._normalize_where(where), limit=limit, include=["metadatas"])

    def get_semesters(self) -> set[str]:
        """Get all unique semesters from the database"""
        results = self._text.get(include=["metadatas"])
        return {meta.get("semester") for meta in results["metadatas"] if meta and "semester" in meta}

    def get_subjects(self, semester: str) -> set[str]:
        """Get all unique subjects for a given semester"""
        results = self._text.get(
            where=self._normalize_where({"semester": semester}),
            include=["metadatas"]
        )
        return {meta.get("subject") for meta in results["metadatas"] if meta and "subject" in meta}

    def get_pdfs(self, semester: str, subject: str) -> List[dict]:
        """Get all PDFs for a given semester and subject"""
        results = self._text.get(
            where=self._normalize_where({
                "semester": semester,
                "subject": subject,
                "type": "pdf"
            }),
            include=["metadatas", "documents"]
        )
        pdfs = []
        seen = set()
        for meta, doc in zip(results["metadatas"], results["documents"]):
            if meta and "pdf_id" in meta and meta["pdf_id"] not in seen:
                seen.add(meta["pdf_id"])
                pdfs.append({
                    "id": meta["pdf_id"],
                    "name": meta.get("pdf_name", "Unknown"),
                    "subject": meta["subject"],
                    "size": meta.get("pdf_size", 0)
                })
        return pdfs

    def get_pdf_path(self, pdf_id: str) -> Optional[str]:
        """Get the file path for a given PDF ID"""
        results = self._text.get(
            where=self._normalize_where({
                "pdf_id": pdf_id,
                "type": "pdf"
            }),
            include=["metadatas"]
        )
        if results["metadatas"]:
            return results["metadatas"][0].get("file_path")
        return None

    def similarity_search(self, query: str, n_results: int = 5) -> List[str]:
        """Search for documents similar to the query"""
        results = self._text.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas"]
        )
        return [doc for doc in results["documents"][0] if doc]
