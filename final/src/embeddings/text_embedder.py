from __future__ import annotations

from typing import Iterable, List
from sentence_transformers import SentenceTransformer


class TextEmbedder:
    def __init__(self, config) -> None:
        model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        if isinstance(config, dict) and 'models' in config:
            model_name = config['models'].get('text', model_name)
        elif hasattr(config, 'models'):
            model_name = getattr(config.models, 'text', model_name)
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=False, normalize_embeddings=True)
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
                        normalized.append(e)  # last resort; should already be a list
            return normalized
        if hasattr(embeddings, 'tolist'):
            return embeddings.tolist()
        try:
            return list(embeddings)
        except Exception:
            return embeddings
