"""Pydantic models for docstore."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocSource(str, Enum):
    """Where the documentation was fetched from."""

    GITHUB = "github"
    GITLAB = "gitlab"
    READTHEDOCS = "readthedocs"
    LLMS_TXT = "llms_txt"
    PYPI_DESCRIPTION = "pypi_description"
    LOCAL = "local"


class ProjectMetadata(BaseModel):
    """Metadata about a Python project from PyPI."""

    name: str
    version: str
    summary: str | None = None
    home_page: str | None = None
    project_urls: dict[str, str] = Field(default_factory=dict)
    repository_url: str | None = None
    documentation_url: str | None = None
    license: str | None = None
    author: str | None = None
    keywords: list[str] = Field(default_factory=list)

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords(cls, v: Any) -> list[str]:
        """Handle keywords that may be a string, list, or None."""
        if v is None:
            return []
        if isinstance(v, str):
            # Split comma-separated string
            return [k.strip() for k in v.split(",") if k.strip()]
        if isinstance(v, list):
            return v
        return []


class DocumentChunk(BaseModel):
    """A chunk of documentation ready for embedding."""

    id: str
    project: str
    version: str
    source_file: str
    title: str | None = None
    content: str
    chunk_index: int
    source: DocSource
    tags: list[str] = Field(default_factory=list)


class ProjectInfo(BaseModel):
    """Information about an indexed project."""

    name: str
    version: str
    source: DocSource
    indexed_at: datetime
    chunk_count: int
    tags: list[str] = Field(default_factory=list)


class IndexRequest(BaseModel):
    """Request to index a project."""

    package: str
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    force: bool = False


class IndexRequirementsRequest(BaseModel):
    """Request to index from requirements.txt content."""

    requirements: str
    tags: list[str] = Field(default_factory=list)
    force: bool = False


class SearchRequest(BaseModel):
    """Request to search documentation."""

    query: str
    n_results: int = 10
    projects: list[str] | None = None
    tags: list[str] | None = None
    auto_index: bool = True  # Auto-index missing projects from PyPI


class SearchResult(BaseModel):
    """A single search result."""

    project: str
    version: str
    source_file: str
    title: str | None
    content: str
    score: float
    tags: list[str]


class SearchResponse(BaseModel):
    """Response from a search query."""

    query: str
    results: list[SearchResult]


class ProjectListResponse(BaseModel):
    """Response listing all indexed projects."""

    projects: list[ProjectInfo]


class StatusResponse(BaseModel):
    """General status response."""

    status: str
    message: str
    details: dict | None = None
