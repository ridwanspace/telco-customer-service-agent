from __future__ import annotations

import pickle
from pathlib import Path

import faiss
import numpy as np

from src.rag.ingestion import Chunk


class VectorStore:
    """FAISS-based vector store for chunk embeddings."""

    def __init__(self, dimension: int = 3072) -> None:
        self.dimension = dimension
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(dimension)
        self.chunks: list[Chunk] = []

    @property
    def count(self) -> int:
        """Number of vectors in the index."""
        return self.index.ntotal

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Add chunks and their embeddings to the index."""
        if not chunks:
            return

        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(
        self, query_embedding: list[float], top_k: int = 3, threshold: float = 0.3
    ) -> list[tuple[Chunk, float]]:
        """Search for similar chunks. Returns (chunk, score) pairs above threshold."""
        if self.count == 0:
            return []

        query_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vec)

        scores, indices = self.index.search(query_vec, min(top_k, self.count))

        results: list[tuple[Chunk, float]] = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx == -1 or score < threshold:
                continue
            results.append((self.chunks[idx], float(score)))

        return results

    def save(self, path: str) -> None:
        """Persist the FAISS index and chunk metadata to disk."""
        index_path = Path(path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(index_path.with_suffix(".faiss")))

        with index_path.with_suffix(".pkl").open("wb") as f:
            pickle.dump(self.chunks, f)

    def load(self, path: str) -> None:
        """Load a FAISS index and chunk metadata from disk."""
        index_path = Path(path)

        faiss_file = index_path.with_suffix(".faiss")
        pkl_file = index_path.with_suffix(".pkl")

        if not faiss_file.exists() or not pkl_file.exists():
            msg = f"Index files not found at {path}"
            raise FileNotFoundError(msg)

        self.index = faiss.read_index(str(faiss_file))
        self.dimension = self.index.d

        with pkl_file.open("rb") as f:
            self.chunks = pickle.load(f)  # noqa: S301
