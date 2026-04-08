"""Tests for knowledge base ingestion and chunking."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.rag.ingestion import chunk_document, load_knowledge_base


class TestChunkDocument:
    """Tests for chunk_document function."""

    def test_extracts_bullets_with_title_prefix(self, tmp_path: Path) -> None:
        doc = tmp_path / "test.md"
        doc.write_text("# My Title\n\n* First bullet\n* Second bullet\n")

        chunks = chunk_document(doc)

        assert len(chunks) == 2
        assert chunks[0].content == "[My Title] First bullet"
        assert chunks[1].content == "[My Title] Second bullet"

    def test_source_is_filename_stem(self, tmp_path: Path) -> None:
        doc = tmp_path / "billing_policy.md"
        doc.write_text("# Billing\n\n* Some policy\n")

        chunks = chunk_document(doc)

        assert chunks[0].source == "billing_policy"

    def test_handles_dash_bullets(self, tmp_path: Path) -> None:
        doc = tmp_path / "test.md"
        doc.write_text("# Title\n\n- Dash bullet\n")

        chunks = chunk_document(doc)

        assert len(chunks) == 1
        assert chunks[0].content == "[Title] Dash bullet"

    def test_empty_document_returns_no_chunks(self, tmp_path: Path) -> None:
        doc = tmp_path / "empty.md"
        doc.write_text("# Empty Doc\n\nNo bullets here.\n")

        chunks = chunk_document(doc)

        assert len(chunks) == 0

    def test_each_chunk_has_unique_id(self, tmp_path: Path) -> None:
        doc = tmp_path / "test.md"
        doc.write_text("# Title\n\n* A\n* B\n* C\n")

        chunks = chunk_document(doc)

        ids = [c.chunk_id for c in chunks]
        assert len(set(ids)) == 3


class TestLoadKnowledgeBase:
    """Tests for load_knowledge_base function."""

    def test_loads_all_markdown_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("# A\n\n* Item A\n")
        (tmp_path / "b.md").write_text("# B\n\n* Item B\n")

        chunks = load_knowledge_base(str(tmp_path))

        assert len(chunks) == 2

    def test_raises_on_missing_directory(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_knowledge_base("/nonexistent/path")

    def test_loads_real_knowledge_base(self) -> None:
        chunks = load_knowledge_base("knowledge_base")

        assert len(chunks) == 12
        sources = {c.source for c in chunks}
        assert sources == {"billing_policy", "service_plans", "troubleshooting_guide"}
