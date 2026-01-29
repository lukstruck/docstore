"""FastAPI HTTP server for docstore."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console

from .config import settings
from .indexer import DocIndexer
from .models import (
    IndexRequest,
    IndexRequirementsRequest,
    ProjectListResponse,
    SearchRequest,
    SearchResponse,
    StatusResponse,
)
from .search_service import SearchOptions, SearchService
from .store import DocStore

console = Console()

# Global instances
store: DocStore | None = None
indexer: DocIndexer | None = None
search_service: SearchService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global store, indexer, search_service
    console.print("[bold green]Starting docstore server...[/bold green]")

    store = DocStore()
    indexer = DocIndexer(store)
    search_service = SearchService(store, indexer)

    yield

    if indexer:
        await indexer.close()
    console.print("[bold yellow]Shutting down docstore server[/bold yellow]")


app = FastAPI(
    title="Docstore",
    description="Python documentation store with semantic search",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> StatusResponse:
    """Health check endpoint."""
    return StatusResponse(status="ok", message="Docstore is running")


@app.get("/stats")
async def get_stats() -> dict:
    """Get storage statistics."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return store.get_stats()


@app.get("/projects", response_model=ProjectListResponse)
async def list_projects() -> ProjectListResponse:
    """List all indexed projects."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return ProjectListResponse(projects=store.list_projects())


@app.get("/projects/{project}")
async def get_project(project: str, version: str | None = None):
    """Get info about a specific project."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    project_info = store.get_project(project, version)
    if not project_info:
        raise HTTPException(status_code=404, detail=f"Project {project} not found")

    return project_info


@app.delete("/projects/{project}")
async def delete_project(project: str, version: str | None = None) -> StatusResponse:
    """Delete a project from the store."""
    if not store:
        raise HTTPException(status_code=503, detail="Store not initialized")

    deleted = store.delete_project(project, version)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Project {project} not found")

    return StatusResponse(
        status="ok",
        message=f"Deleted {deleted} chunks",
        details={"project": project, "version": version, "chunks_deleted": deleted},
    )


@app.post("/index", response_model=StatusResponse)
async def index_package(request: IndexRequest) -> StatusResponse:
    """Index a single package."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        result = await indexer.index_package(request)
        return StatusResponse(
            status="ok",
            message=f"Indexed {result.name} v{result.version}",
            details={
                "name": result.name,
                "version": result.version,
                "source": result.source.value,
                "chunks": result.chunk_count,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index/requirements", response_model=StatusResponse)
async def index_requirements(request: IndexRequirementsRequest) -> StatusResponse:
    """Index packages from requirements.txt content."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        results = await indexer.index_requirements(
            request.requirements,
            tags=request.tags,
            force=request.force,
        )

        return StatusResponse(
            status="ok",
            message=f"Indexed {len(results)} packages",
            details={
                "indexed": [
                    {"name": r.name, "version": r.version, "chunks": r.chunk_count}
                    for r in results
                ]
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Search documentation.

    If projects are specified and not indexed, they will be auto-indexed from PyPI
    (unless auto_index=false).
    """
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")

    from .store import ProjectNotFoundError

    try:
        options = SearchOptions(
            query=request.query,
            n_results=request.n_results,
            projects=request.projects,
            tags=request.tags,
            auto_index=request.auto_index,
        )
        outcome = await search_service.search(options)
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Projects not indexed",
                "missing_projects": e.projects,
                "hint": "Use auto_index=true or index the projects first",
            },
        )

    if not outcome.results and outcome.failed_to_index:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Could not index requested projects",
                "failed": outcome.failed_to_index,
            },
        )

    return SearchResponse(query=request.query, results=outcome.results)


@app.post("/update/{project}", response_model=StatusResponse)
async def update_project(project: str) -> StatusResponse:
    """Update a project to the latest version."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        result = await indexer.update_project(project)
        return StatusResponse(
            status="ok",
            message=f"Updated {result.name} to v{result.version}",
            details={
                "name": result.name,
                "version": result.version,
                "source": result.source.value,
                "chunks": result.chunk_count,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run():
    """Run the server."""
    import uvicorn

    console.print(f"[bold]Starting docstore on http://{settings.host}:{settings.port}[/bold]")
    uvicorn.run(
        "docstore.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
