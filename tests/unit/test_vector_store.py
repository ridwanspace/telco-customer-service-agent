"""Tests for FAISS vector store."""

from __future__ import annotations

import numpy as np
import pytest

from src.rag.ingestion import Chunk
from src.rag.vector_store import VectorStore


class TestVectorStore:
    """Tests for VectorStore class."""

    def _make_chunks(self, n: int) -> list[Chunk]:
        return [Chunk(content=f"chunk {i}", source=f"doc_{i}") for i in range(n)]

    def _make_embeddings(self, n: int, dim: int = 128) -> list[list[float]]:
        rng = np.random.default_rng(42)
        vecs = rng.standard_normal((n, dim)).astype(np.float32)
        return [v.tolist() for v in vecs]

    def test_add_and_count(self) -> None:
        vs = VectorStore(dimension=128)
        chunks = self._make_chunks(5)
        embeddings = self._make_embeddings(5)

        vs.add(chunks, embeddings)

        assert vs.count == 5

    def test_search_returns_results(self) -> None:
        vs = VectorStore(dimension=128)
        chunks = self._make_chunks(5)
        embeddings = self._make_embeddings(5)
        vs.add(chunks, embeddings)

        results = vs.search(embeddings[0], top_k=3, threshold=0.0)

        assert len(results) > 0
        assert results[0][0].content == "chunk 0"

    def test_search_empty_store(self) -> None:
        vs = VectorStore(dimension=128)

        results = vs.search([0.0] * 128, top_k=3, threshold=0.0)

        assert results == []

    def test_search_respects_threshold(self) -> None:
        vs = VectorStore(dimension=128)
        chunks = self._make_chunks(3)
        embeddings = self._make_embeddings(3)
        vs.add(chunks, embeddings)

        results = vs.search(embeddings[0], top_k=3, threshold=0.99)

        # Only the exact match should pass a very high threshold
        assert len(results) <= 1

    def test_save_and_load(self, tmp_path: pytest.TempPathFactory) -> None:
        vs = VectorStore(dimension=128)
        chunks = self._make_chunks(3)
        embeddings = self._make_embeddings(3)
        vs.add(chunks, embeddings)

        path = str(tmp_path / "test_index")
        vs.save(path)

        vs2 = VectorStore()
        vs2.load(path)

        assert vs2.count == 3
        assert vs2.chunks[0].content == "chunk 0"

    def test_load_missing_raises(self) -> None:
        vs = VectorStore()

        with pytest.raises(FileNotFoundError):
            vs.load("/nonexistent/index")

    def test_add_empty(self) -> None:
        vs = VectorStore(dimension=128)

        vs.add([], [])

        assert vs.count == 0
