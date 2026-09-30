from sentence_transformers import SentenceTransformer
import numpy as np

# Loaded once, at startup — turns text into meaning-vectors, 100% local.
_model = SentenceTransformer("all-MiniLM-L6-v2")

# How similar two questions need to be (0 to 1) to count as the same
# question. 1.0 = identical meaning.
SIMILARITY_THRESHOLD = 0.65


class SemanticCache:
    def __init__(self):
        self._entries: list[dict] = []

    def find_similar(self, prompt: str) -> tuple[str | None, float]:
        query_embedding = _model.encode(prompt, normalize_embeddings=True)

        best_score = -1.0
        best_cache_key = None

        for entry in self._entries:
            score = float(np.dot(query_embedding, entry["embedding"]))
            if score > best_score:
                best_score = score
                best_cache_key = entry["cache_key"]

        if best_cache_key is not None and best_score >= SIMILARITY_THRESHOLD:
            return best_cache_key, best_score

        return None, best_score

    def add(self, prompt: str, cache_key: str) -> None:
        embedding = _model.encode(prompt, normalize_embeddings=True)
        self._entries.append({"prompt": prompt, "embedding": embedding, "cache_key": cache_key})


semantic_cache = SemanticCache()