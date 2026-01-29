"""Orchestrates the indexing pipeline: fetch -> convert -> chunk -> store."""

import re
import tempfile
from pathlib import Path

from packaging.requirements import Requirement
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .chunker import DocChunker
from .config import settings
from .converter import DocConverter
from .fetcher import PyPIFetcher
from .models import DocSource, IndexRequest, ProjectInfo
from .store import DocStore

console = Console()


class DocIndexer:
    """Indexes Python package documentation."""

    def __init__(self, store: DocStore | None = None):
        self.store = store or DocStore()
        self.fetcher = PyPIFetcher()
        self.converter = DocConverter()
        self.chunker = DocChunker()

    async def close(self):
        await self.fetcher.close()

    async def index_package(self, request: IndexRequest) -> ProjectInfo:
        """Index documentation for a single package."""
        package = request.package.lower()
        console.print(f"\n[bold blue]Indexing {package}...[/bold blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Check if already indexed
            if not request.force:
                existing = self.store.get_project(package)
                if existing:
                    if request.version and existing.version != request.version:
                        pass  # Continue to index different version
                    else:
                        console.print(f"[yellow]{package} already indexed (use force=True to reindex)[/yellow]")
                        return existing

            # Fetch metadata
            task = progress.add_task("Fetching metadata...", total=None)
            metadata = await self.fetcher.get_metadata(package, request.version)
            progress.update(task, description=f"Found {metadata.name} v{metadata.version}")

            # Fetch documentation
            progress.update(task, description="Fetching documentation...")
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                source, doc_files = await self.fetcher.fetch_docs(metadata, output_dir)

                if not doc_files:
                    console.print(
                        f"[yellow]Warning: No documentation found for {package}[/yellow]\n"
                        f"[dim]  No docs from repository, ReadTheDocs, or llms.txt[/dim]"
                    )
                    # Create minimal entry
                    return ProjectInfo(
                        name=metadata.name,
                        version=metadata.version,
                        source=DocSource.PYPI_DESCRIPTION,
                        indexed_at=__import__("datetime").datetime.now(),
                        chunk_count=0,
                        tags=request.tags,
                    )

                # Warn if only PyPI description (limited content)
                if source == DocSource.PYPI_DESCRIPTION:
                    console.print(
                        f"[yellow]Note: Only PyPI description available for {package}[/yellow]\n"
                        f"[dim]  Search results will be limited. Full docs not accessible.[/dim]"
                    )
                else:
                    progress.update(task, description=f"Found {len(doc_files)} doc files from {source.value}")

                # Convert and chunk
                progress.update(task, description="Processing documents...")
                all_chunks = []

                for doc_file in doc_files:
                    content = self.converter.convert_file(doc_file)
                    if not content:
                        continue

                    title = self.converter.extract_title(content, doc_file)
                    relative_path = str(doc_file.relative_to(output_dir))

                    chunks = self.chunker.chunk_document(
                        content=content,
                        project=metadata.name,
                        version=metadata.version,
                        source_file=relative_path,
                        source=source,
                        title=title,
                        tags=request.tags,
                    )
                    all_chunks.extend(chunks)

                # Delete old version if exists
                if request.force:
                    self.store.delete_project(metadata.name)

                # Store chunks
                progress.update(task, description=f"Storing {len(all_chunks)} chunks...")
                self.store.add_chunks(all_chunks)

            progress.update(task, description="[green]Done![/green]")

        project_info = ProjectInfo(
            name=metadata.name,
            version=metadata.version,
            source=source,
            indexed_at=__import__("datetime").datetime.now(),
            chunk_count=len(all_chunks),
            tags=request.tags,
        )

        # Final summary with context
        if source == DocSource.PYPI_DESCRIPTION:
            console.print(
                f"[yellow]✓ Indexed {metadata.name} v{metadata.version}: {len(all_chunks)} chunks "
                f"(PyPI description only)[/yellow]"
            )
        elif len(all_chunks) < 5:
            console.print(
                f"[yellow]✓ Indexed {metadata.name} v{metadata.version}: {len(all_chunks)} chunks "
                f"(limited documentation)[/yellow]"
            )
        else:
            console.print(
                f"[green]✓ Indexed {metadata.name} v{metadata.version}: {len(all_chunks)} chunks[/green]"
            )
        return project_info

    async def index_requirements(
        self,
        requirements_content: str,
        tags: list[str] | None = None,
        force: bool = False,
    ) -> list[ProjectInfo]:
        """Index all packages from requirements.txt content."""
        tags = tags or []
        results = []

        # Parse requirements
        packages = self._parse_requirements(requirements_content)
        console.print(f"[bold]Found {len(packages)} packages to index[/bold]")

        for package, version in packages:
            try:
                request = IndexRequest(
                    package=package,
                    version=version,
                    tags=tags,
                    force=force,
                )
                result = await self.index_package(request)
                results.append(result)
            except Exception as e:
                console.print(f"[red]Failed to index {package}: {e}[/red]")

        return results

    def _parse_requirements(self, content: str) -> list[tuple[str, str | None]]:
        """Parse requirements.txt content into (package, version) tuples."""
        packages = []

        for line in content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Skip URLs
            if line.startswith("http://") or line.startswith("https://") or line.startswith("git+"):
                continue

            try:
                req = Requirement(line)
                # Extract pinned version if available
                version = None
                for spec in req.specifier:
                    if spec.operator == "==":
                        version = spec.version
                        break

                packages.append((req.name, version))
            except Exception:
                # Try simple regex fallback
                match = re.match(r"^([\w-]+)", line)
                if match:
                    packages.append((match.group(1), None))

        return packages

    async def update_project(self, package: str) -> ProjectInfo:
        """Update an existing project to the latest version."""
        return await self.index_package(
            IndexRequest(package=package, force=True)
        )
