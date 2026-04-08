"""Standalone script to ingest the knowledge base into FAISS."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.rag.embeddings import embed_texts
from src.rag.ingestion import load_knowledge_base
from src.rag.vector_store import VectorStore


def main() -> None:
    """Ingest knowledge base documents into FAISS vector store."""
    print(f"Loading knowledge base from: {settings.knowledge_base_path}")
    chunks = load_knowledge_base(settings.knowledge_base_path)
    print(f"Loaded {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  [{chunk.source}] {chunk.content[:80]}...")

    print(f"\nGenerating embeddings with {settings.embedding_model}...")
    texts = [c.content for c in chunks]
    embeddings = embed_texts(texts)
    print(f"Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    print("\nBuilding FAISS index...")
    vs = VectorStore(dimension=len(embeddings[0]))
    vs.add(chunks, embeddings)
    print(f"Index contains {vs.count} vectors")

    print(f"\nSaving to {settings.faiss_index_path}...")
    vs.save(settings.faiss_index_path)
    print("Done!")


if __name__ == "__main__":
    main()
