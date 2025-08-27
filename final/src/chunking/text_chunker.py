from typing import Iterable, List


def split_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    if not text:
        return []

    paragraphs: List[str] = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(para)
            continue
        start = 0
        while start < len(para):
            end = min(start + max_chars, len(para))
            chunk = para[start:end]
            chunks.append(chunk)
            if end == len(para):
                break
            start = max(0, end - overlap)
    return chunks
