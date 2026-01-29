"""Split documentation into semantic chunks for embedding."""

import hashlib
import re
from dataclasses import dataclass

from .config import settings
from .models import DocSource, DocumentChunk


@dataclass
class ChunkConfig:
    """Configuration for chunking."""

    chunk_size: int = settings.chunk_size
    chunk_overlap: int = settings.chunk_overlap
    min_chunk_size: int = 100  # Don't create tiny chunks


class DocChunker:
    """Splits documentation into semantic chunks."""

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    def chunk_document(
        self,
        content: str,
        project: str,
        version: str,
        source_file: str,
        source: DocSource,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> list[DocumentChunk]:
        """Split a document into chunks with metadata."""
        tags = tags or []

        # First, try to split by headers for semantic chunking
        sections = self._split_by_headers(content)

        chunks = []
        chunk_index = 0

        for section_title, section_content in sections:
            # Use section title if available, else document title
            chunk_title = section_title or title

            # Split large sections further
            section_chunks = self._split_text(section_content)

            for chunk_text in section_chunks:
                if len(chunk_text.strip()) < self.config.min_chunk_size:
                    continue

                chunk_id = self._generate_id(project, version, source_file, chunk_index)

                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        project=project,
                        version=version,
                        source_file=source_file,
                        title=chunk_title,
                        content=chunk_text.strip(),
                        chunk_index=chunk_index,
                        source=source,
                        tags=tags,
                    )
                )
                chunk_index += 1

        return chunks

    def _split_by_headers(self, content: str) -> list[tuple[str | None, str]]:
        """Split content by markdown headers."""
        # Match headers (# to ####)
        header_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

        sections = []
        last_end = 0
        current_title = None

        for match in header_pattern.finditer(content):
            # Get content before this header
            if match.start() > last_end:
                text = content[last_end : match.start()].strip()
                if text:
                    sections.append((current_title, text))

            current_title = match.group(2).strip()
            last_end = match.end()

        # Get remaining content
        remaining = content[last_end:].strip()
        if remaining:
            sections.append((current_title, remaining))

        # If no headers found, return whole content
        if not sections:
            return [(None, content)]

        return sections

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks respecting sentence boundaries."""
        if len(text) <= self.config.chunk_size:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by paragraphs first
        paragraphs = re.split(r"\n\n+", text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph fits, add it
            if len(current_chunk) + len(para) + 2 <= self.config.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Current chunk is full
                if current_chunk:
                    chunks.append(current_chunk)

                # If paragraph itself is too large, split by sentences
                if len(para) > self.config.chunk_size:
                    sentence_chunks = self._split_by_sentences(para)
                    chunks.extend(sentence_chunks[:-1])
                    current_chunk = sentence_chunks[-1] if sentence_chunks else ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap between chunks
        return self._add_overlap(chunks)

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text by sentences when paragraphs are too large."""
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= self.config.chunk_size:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    chunks.append(current)
                current = sentence

        if current:
            chunks.append(current)

        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between chunks for context continuity."""
        if len(chunks) <= 1 or self.config.chunk_overlap == 0:
            return chunks

        result = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # Get overlap from end of previous chunk
            overlap_text = self._get_overlap_text(prev_chunk)

            if overlap_text and not current_chunk.startswith(overlap_text):
                result.append(f"...{overlap_text}\n\n{current_chunk}")
            else:
                result.append(current_chunk)

        return result

    def _get_overlap_text(self, text: str) -> str:
        """Get text for overlap from end of chunk."""
        if len(text) <= self.config.chunk_overlap:
            return text

        # Try to break at sentence boundary
        end_text = text[-self.config.chunk_overlap :]
        sentence_match = re.search(r"[.!?]\s+", end_text)

        if sentence_match:
            return end_text[sentence_match.end() :]
        return end_text

    def _generate_id(self, project: str, version: str, source_file: str, index: int) -> str:
        """Generate a unique chunk ID."""
        key = f"{project}:{version}:{source_file}:{index}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
