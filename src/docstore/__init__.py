"""Docstore - Python documentation store with semantic search."""

from .models import (
    DocumentChunk,
    DocSource,
    IndexRequest,
    ProjectInfo,
    SearchRequest,
    SearchResult,
)
from .store import DocStore
from .indexer import DocIndexer

__version__ = "0.1.0"
__all__ = [
    "DocStore",
    "DocIndexer",
    "DocumentChunk",
    "DocSource",
    "IndexRequest",
    "ProjectInfo",
    "SearchRequest",
    "SearchResult",
]
