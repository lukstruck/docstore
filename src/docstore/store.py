"""ChromaDB storage backend for documentation chunks."""

from datetime import datetime
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console

from .config import settings
from .models import DocumentChunk, DocSource, ProjectInfo, SearchResult

console = Console()

# ChromaDB has a max batch size limit for embeddings
MAX_BATCH_SIZE = 5000


class ProjectNotFoundError(Exception):
    """Raised when requested projects are not indexed."""

    def __init__(self, projects: list[str]):
        self.projects = projects
        super().__init__(f"Projects not indexed: {', '.join(projects)}")


class DocStore:
    """ChromaDB-backed storage for documentation chunks."""

    def __init__(self):
        settings.ensure_dirs()

        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._projects_cache: dict[str, ProjectInfo] | None = None

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add document chunks to the store.

        Handles large chunk lists by batching to avoid ChromaDB's batch size limit.
        """
        if not chunks:
            return 0

        total_chunks = len(chunks)

        # Process in batches to avoid ChromaDB's batch size limit
        for batch_start in range(0, total_chunks, MAX_BATCH_SIZE):
            batch_end = min(batch_start + MAX_BATCH_SIZE, total_chunks)
            batch = chunks[batch_start:batch_end]

            if total_chunks > MAX_BATCH_SIZE:
                console.print(
                    f"  [dim]Storing batch {batch_start // MAX_BATCH_SIZE + 1}/"
                    f"{(total_chunks + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE} "
                    f"({len(batch)} chunks)[/dim]"
                )

            ids = [chunk.id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [
                {
                    "project": chunk.project,
                    "version": chunk.version,
                    "source_file": chunk.source_file,
                    "title": chunk.title or "",
                    "chunk_index": chunk.chunk_index,
                    "source": chunk.source.value,
                    "tags": ",".join(chunk.tags),
                    "indexed_at": datetime.now().isoformat(),
                }
                for chunk in batch
            ]

            # Upsert to handle updates
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        self._projects_cache = None  # Invalidate cache
        return total_chunks

    def _resolve_project_names(self, projects: list[str]) -> tuple[list[str], list[str]]:
        """Resolve project names with case-insensitive matching.

        Returns (resolved_names, unresolved_names).
        """
        indexed = {p.name.lower(): p.name for p in self.list_projects()}
        resolved = []
        unresolved = []

        for proj in projects:
            if proj.lower() in indexed:
                resolved.append(indexed[proj.lower()])
            else:
                unresolved.append(proj)

        return resolved, unresolved

    def search(
        self,
        query: str,
        n_results: int = 10,
        projects: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[SearchResult]:
        """Search for relevant documentation chunks.

        Project filtering is case-insensitive.
        """
        # Resolve project names (case-insensitive)
        resolved_projects = None
        if projects:
            resolved_projects, unresolved = self._resolve_project_names(projects)
            if unresolved:
                # Return unresolved for caller to handle (e.g., auto-index)
                raise ProjectNotFoundError(unresolved)
            if not resolved_projects:
                return []

        where_filter = self._build_filter(resolved_projects, tags)

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                distance = results["distances"][0][i] if results["distances"] else 0

                # Convert distance to similarity score (cosine distance to similarity)
                score = 1 - distance

                search_results.append(
                    SearchResult(
                        project=meta["project"],
                        version=meta["version"],
                        source_file=meta["source_file"],
                        title=meta["title"] or None,
                        content=doc,
                        score=score,
                        tags=meta["tags"].split(",") if meta["tags"] else [],
                    )
                )

        return search_results

    def _build_filter(
        self, projects: list[str] | None, tags: list[str] | None
    ) -> dict[str, Any] | None:
        """Build ChromaDB where filter."""
        conditions = []

        if projects:
            if len(projects) == 1:
                conditions.append({"project": {"$eq": projects[0]}})
            else:
                conditions.append({"project": {"$in": projects}})

        if tags:
            # Tags are stored as comma-separated string, use contains
            tag_conditions = [{"tags": {"$contains": tag}} for tag in tags]
            if len(tag_conditions) == 1:
                conditions.extend(tag_conditions)
            else:
                conditions.append({"$or": tag_conditions})

        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    def delete_project(self, project: str, version: str | None = None) -> int:
        """Delete all chunks for a project (optionally specific version)."""
        where: dict[str, Any] = {"project": {"$eq": project}}
        if version:
            where = {"$and": [where, {"version": {"$eq": version}}]}

        # Get IDs to delete
        results = self.collection.get(where=where, include=[])

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            self._projects_cache = None
            return len(results["ids"])

        return 0

    def list_projects(self) -> list[ProjectInfo]:
        """List all indexed projects."""
        if self._projects_cache is not None:
            return list(self._projects_cache.values())

        # Get all unique projects from metadata
        results = self.collection.get(include=["metadatas"])

        projects: dict[str, ProjectInfo] = {}

        for meta in results["metadatas"]:
            project_name = meta["project"]
            version = meta["version"]
            key = f"{project_name}:{version}"

            if key not in projects:
                projects[key] = ProjectInfo(
                    name=project_name,
                    version=version,
                    source=DocSource(meta["source"]),
                    indexed_at=datetime.fromisoformat(meta["indexed_at"]),
                    chunk_count=0,
                    tags=meta["tags"].split(",") if meta["tags"] else [],
                )

            projects[key].chunk_count += 1

        self._projects_cache = projects
        return list(projects.values())

    def get_project(self, project: str, version: str | None = None) -> ProjectInfo | None:
        """Get info about a specific project."""
        projects = self.list_projects()

        for p in projects:
            if p.name == project:
                if version is None or p.version == version:
                    return p

        return None

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        count = self.collection.count()
        projects = self.list_projects()

        return {
            "total_chunks": count,
            "total_projects": len(projects),
            "projects": [{"name": p.name, "version": p.version, "chunks": p.chunk_count} for p in projects],
        }
