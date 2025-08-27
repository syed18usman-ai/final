from __future__ import annotations

from typing import List
from PIL import Image
from sentence_transformers import SentenceTransformer
import io
import logging

logger = logging.getLogger(__name__)


class ImageEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=False, normalize_embeddings=True)
            # Normalize to list[list[float]] regardless of backend
            if isinstance(embeddings, list):
                normalized: List[List[float]] = []
                for e in embeddings:
                    if hasattr(e, 'tolist'):
                        normalized.append(e.tolist())
                    else:
                        try:
                            normalized.append(list(e))
                        except Exception:
                            normalized.append(e)
                return normalized
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            try:
                return list(embeddings)
            except Exception:
                return embeddings
        except Exception as e:
            logger.error(f"Failed to embed text with CLIP: {e}")
            return []

    def embed_bytes(self, images: List[bytes]) -> tuple[List[List[float]], List[int]]:
        if not images:
            return [], []
        
        valid_images = []
        valid_indices = []
        for i, img_bytes in enumerate(images):
            try:
                # Open and convert to RGB
                pil_img = Image.open(io.BytesIO(img_bytes))
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                
                # Ensure reasonable dimensions
                if pil_img.size[0] < 10 or pil_img.size[1] < 10:
                    logger.warning(f"Skipping image {i}: too small ({pil_img.size})")
                    continue
                
                valid_images.append(pil_img)
                valid_indices.append(i)
            except Exception as e:
                logger.warning(f"Skipping image {i}: failed to process - {e}")
                continue
        
        if not valid_images:
            return [], []
        
        try:
            embeddings = self.model.encode(valid_images, convert_to_numpy=False, normalize_embeddings=True)
            # Normalize to a list of lists of floats regardless of backend type
            if isinstance(embeddings, list):
                normalized: List[List[float]] = []
                for e in embeddings:
                    if hasattr(e, 'tolist'):
                        normalized.append(e.tolist())
                    else:
                        try:
                            normalized.append(list(e))
                        except Exception:
                            normalized.append(e)
                return normalized, valid_indices
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist(), valid_indices
            try:
                return list(embeddings), valid_indices
            except Exception:
                return embeddings, valid_indices
        except Exception as e:
            logger.error(f"Failed to embed images: {e}")
            return [], []
