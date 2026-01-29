"""Command-line interface for docstore."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import settings
from .indexer import DocIndexer
from .models import IndexRequest
from .store import DocStore

app = typer.Typer(
    name="docstore",
    help="Python documentation store with semantic search",
    no_args_is_help=True,
)
console = Console()


def _run_async(coro):
    """Run async function in sync context."""
    return asyncio.get_event_loop().run_until_complete(coro)


@app.command()
def index(
    package: str = typer.Argument(..., help="PyPI package name to index"),
    version: str | None = typer.Option(None, "--version", "-v", help="Specific version"),
    tags: list[str] = typer.Option([], "--tag", "-t", help="Tags to apply"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reindex"),
):
    """Index documentation for a Python package."""

    async def _index():
        store = DocStore()
        indexer = DocIndexer(store)
        try:
            request = IndexRequest(package=package, version=version, tags=tags, force=force)
            await indexer.index_package(request)
        finally:
            await indexer.close()

    _run_async(_index())


@app.command()
def index_requirements(
    file: Path = typer.Argument(..., help="Path to requirements.txt"),
    tags: list[str] = typer.Option([], "--tag", "-t", help="Tags to apply to all packages"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reindex"),
):
    """Index all packages from a requirements.txt file."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()

    async def _index():
        store = DocStore()
        indexer = DocIndexer(store)
        try:
            await indexer.index_requirements(content, tags=tags, force=force)
        finally:
            await indexer.close()

    _run_async(_index())


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    n: int = typer.Option(5, "--n", "-n", help="Number of results"),
    project: list[str] = typer.Option([], "--project", "-p", help="Filter by project"),
    tag: list[str] = typer.Option([], "--tag", "-t", help="Filter by tag"),
):
    """Search indexed documentation."""
    store = DocStore()
    results = store.search(
        query=query,
        n_results=n,
        projects=project if project else None,
        tags=tag if tag else None,
    )

    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return

    console.print(f"\n[bold]Found {len(results)} results for '{query}'[/bold]\n")

    for i, result in enumerate(results, 1):
        console.print(f"[bold cyan]--- Result {i} ---[/bold cyan]")
        console.print(f"[bold]{result.project}[/bold] v{result.version} | Score: {result.score:.3f}")
        if result.title:
            console.print(f"[dim]Title:[/dim] {result.title}")
        console.print(f"[dim]Source:[/dim] {result.source_file}")
        console.print()
        console.print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
        console.print()


@app.command()
def list_projects():
    """List all indexed projects."""
    store = DocStore()
    projects = store.list_projects()

    if not projects:
        console.print("[yellow]No projects indexed yet[/yellow]")
        return

    table = Table(title="Indexed Projects")
    table.add_column("Project", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Source")
    table.add_column("Chunks", justify="right")
    table.add_column("Tags")

    for p in sorted(projects, key=lambda x: x.name):
        table.add_row(
            p.name,
            p.version,
            p.source.value,
            str(p.chunk_count),
            ", ".join(p.tags) if p.tags else "-",
        )

    console.print(table)


@app.command()
def delete(
    project: str = typer.Argument(..., help="Project to delete"),
    version: str | None = typer.Option(None, "--version", "-v", help="Specific version"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a project from the store."""
    store = DocStore()

    if not yes:
        version_str = f" v{version}" if version else ""
        confirm = typer.confirm(f"Delete {project}{version_str}?")
        if not confirm:
            raise typer.Abort()

    deleted = store.delete_project(project, version)
    if deleted:
        console.print(f"[green]Deleted {deleted} chunks[/green]")
    else:
        console.print(f"[yellow]Project {project} not found[/yellow]")


@app.command()
def stats():
    """Show storage statistics."""
    store = DocStore()
    stats = store.get_stats()

    console.print(f"\n[bold]Docstore Statistics[/bold]")
    console.print(f"Total chunks: {stats['total_chunks']}")
    console.print(f"Total projects: {stats['total_projects']}")

    if stats["projects"]:
        console.print("\n[bold]By project:[/bold]")
        for p in sorted(stats["projects"], key=lambda x: x["chunks"], reverse=True):
            console.print(f"  {p['name']} v{p['version']}: {p['chunks']} chunks")


@app.command()
def serve(
    host: str = typer.Option(settings.host, "--host", "-h", help="Host to bind"),
    port: int = typer.Option(settings.port, "--port", "-p", help="Port to bind"),
):
    """Start the HTTP server."""
    import uvicorn
    from .main import app as fastapi_app

    console.print(f"[bold]Starting docstore server on http://{host}:{port}[/bold]")
    uvicorn.run(fastapi_app, host=host, port=port)


@app.command()
def mcp():
    """Start the MCP server (for Claude integration)."""
    from .mcp_server import run
    run()


if __name__ == "__main__":
    app()
