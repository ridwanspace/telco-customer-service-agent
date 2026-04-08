from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


@dataclass
class Chunk:
    """A single chunk of text from the knowledge base."""

    content: str
    source: str
    chunk_id: str = field(default_factory=lambda: str(uuid4()))


def _extract_title(text: str) -> str:
    """Extract the markdown title (# Title) from document text."""
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "Unknown"


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet points from markdown text."""
    bullets: list[str] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if re.match(r"^[*\-]\s+", line):
            bullet_text = re.sub(r"^[*\-]\s+", "", line).strip()
            if bullet_text:
                bullets.append(bullet_text)
    return bullets


def chunk_document(file_path: Path) -> list[Chunk]:
    """Chunk a single knowledge base document into per-bullet-point chunks.

    Each bullet point is prefixed with the document title for context.
    This strategy works well for structured KB documents with independent facts.
    """
    text = file_path.read_text(encoding="utf-8")
    title = _extract_title(text)
    bullets = _extract_bullets(text)
    source = file_path.stem

    return [
        Chunk(
            content=f"[{title}] {bullet}",
            source=source,
        )
        for bullet in bullets
    ]


def load_knowledge_base(kb_path: str = "knowledge_base") -> list[Chunk]:
    """Load and chunk all documents from the knowledge base directory."""
    kb_dir = Path(kb_path)
    if not kb_dir.exists():
        msg = f"Knowledge base directory not found: {kb_path}"
        raise FileNotFoundError(msg)

    chunks: list[Chunk] = []
    for file_path in sorted(kb_dir.glob("*.md")):
        chunks.extend(chunk_document(file_path))

    return chunks
