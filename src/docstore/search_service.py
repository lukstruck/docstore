"""Search service with auto-indexing support."""

from dataclasses import dataclass
from rich.console import Console

from .indexer import DocIndexer
from .models import IndexRequest, SearchResult
from .store import DocStore, ProjectNotFoundError

console = Console()


@dataclass
class SearchOptions:
    """Options for search."""

    query: str
    n_results: int = 10
    projects: list[str] | None = None
    tags: list[str] | None = None
    auto_index: bool = True


@dataclass
class SearchOutcome:
    """Result of a search operation."""

    results: list[SearchResult]
    auto_indexed: list[str]  # Projects that were auto-indexed
    failed_to_index: list[dict]  # Projects that failed to index with reasons


class SearchService:
    """Search service that handles auto-indexing of missing projects."""

    def __init__(self, store: DocStore, indexer: DocIndexer):
        self.store = store
        self.indexer = indexer

    async def search(self, options: SearchOptions) -> SearchOutcome:
        """Search documentation, auto-indexing missing projects if enabled.

        Args:
            options: Search options including query, filters, and auto_index flag.

        Returns:
            SearchOutcome with results and info about auto-indexed projects.

        Raises:
            ProjectNotFoundError: If auto_index=False and projects aren't indexed.
        """
        auto_indexed = []
        failed_to_index = []

        try:
            results = self.store.search(
                query=options.query,
                n_results=options.n_results,
                projects=options.projects,
                tags=options.tags,
            )
            return SearchOutcome(results=results, auto_indexed=[], failed_to_index=[])

        except ProjectNotFoundError as e:
            if not options.auto_index:
                raise

            # Auto-index missing projects
            console.print(
                f"\n[blue]Auto-indexing missing projects: {', '.join(e.projects)}[/blue]"
            )

            for project in e.projects:
                try:
                    result = await self.indexer.index_package(
                        IndexRequest(package=project)
                    )
                    if result.chunk_count > 0:
                        auto_indexed.append(result.name)
                    else:
                        failed_to_index.append({
                            "project": project,
                            "reason": "No documentation found",
                        })
                except Exception as ex:
                    failed_to_index.append({
                        "project": project,
                        "reason": str(ex),
                    })

            if not auto_indexed:
                # Nothing was indexed, return empty with failures
                return SearchOutcome(
                    results=[],
                    auto_indexed=[],
                    failed_to_index=failed_to_index,
                )

            # Retry search
            try:
                results = self.store.search(
                    query=options.query,
                    n_results=options.n_results,
                    projects=options.projects,
                    tags=options.tags,
                )
            except ProjectNotFoundError:
                # Some projects still missing, search only indexed ones
                results = self.store.search(
                    query=options.query,
                    n_results=options.n_results,
                    projects=auto_indexed,
                    tags=options.tags,
                )

            return SearchOutcome(
                results=results,
                auto_indexed=auto_indexed,
                failed_to_index=failed_to_index,
            )
