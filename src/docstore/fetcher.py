"""Fetch package metadata from PyPI and locate documentation sources."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from rich.console import Console
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import settings
from .models import DocSource, ProjectMetadata

console = Console()


def _create_http_retry():
    """
    Create a retry decorator for HTTP operations.

    Retries on transient network failures (timeouts, connection errors)
    with exponential backoff.
    """
    return retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(
            multiplier=settings.retry_backoff_base,
            max=settings.retry_backoff_max,
        ),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )


class PyPIFetcher:
    """Fetches package metadata and documentation from various sources."""

    PYPI_API = "https://pypi.org/pypi"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.request_timeout)

    async def close(self):
        await self.client.aclose()

    @_create_http_retry()
    async def _get_with_retry(self, url: str, **kwargs) -> httpx.Response:
        """HTTP GET with automatic retry on transient failures."""
        return await self.client.get(url, **kwargs)

    async def get_metadata(self, package: str, version: str | None = None) -> ProjectMetadata:
        """Fetch package metadata from PyPI with automatic retry on network failures."""
        url = f"{self.PYPI_API}/{package}/json"
        if version:
            url = f"{self.PYPI_API}/{package}/{version}/json"

        response = await self._get_with_retry(url)
        response.raise_for_status()
        data = response.json()

        info = data["info"]
        project_urls = info.get("project_urls") or {}

        # Try to find repository URL
        repo_url = self._find_repo_url(info, project_urls)
        docs_url = self._find_docs_url(info, project_urls)

        return ProjectMetadata(
            name=info["name"],
            version=info["version"],
            summary=info.get("summary"),
            home_page=info.get("home_page"),
            project_urls=project_urls,
            repository_url=repo_url,
            documentation_url=docs_url,
            license=info.get("license"),
            author=info.get("author"),
            keywords=info.get("keywords") or [],
        )

    def _find_repo_url(self, info: dict, project_urls: dict) -> str | None:
        """Extract repository URL from package metadata."""
        # Check project_urls for common keys
        repo_keys = ["Repository", "Source", "Source Code", "GitHub", "Code", "Homepage"]
        for key in repo_keys:
            if key in project_urls:
                url = project_urls[key]
                if self._is_repo_url(url):
                    return self._normalize_repo_url(url)

        # Check home_page
        home = info.get("home_page")
        if home and self._is_repo_url(home):
            return self._normalize_repo_url(home)

        return None

    def _find_docs_url(self, info: dict, project_urls: dict) -> str | None:
        """Extract documentation URL from package metadata."""
        docs_keys = ["Documentation", "Docs", "docs", "documentation"]
        for key in docs_keys:
            if key in project_urls:
                return project_urls[key]
        return info.get("docs_url")

    def _is_valid_llms_content(self, content: str) -> bool:
        """
        Validate that content looks like documentation, not HTML/JSON garbage.

        Many URLs return error pages or redirects as HTML/JSON instead of the
        expected llms.txt content. This validation prevents indexing such garbage.
        """
        start = content[:500].strip().lower()

        # Reject HTML (case-insensitive check on first 500 chars)
        if start.startswith(("<!doctype", "<html", "<script")):
            return False

        # Reject JSON
        stripped = content.strip()
        if stripped.startswith(("{", "[")):
            return False

        # Reject JavaScript (check in first 500 chars)
        if "window." in start or "function(" in start:
            return False

        # Require documentation structure: headers, code blocks, or multiple paragraphs
        has_headers = bool(re.search(r"^#+\s+\w", content, re.MULTILINE))
        has_code = "```" in content
        has_paragraphs = content.count("\n\n") > 2

        return has_headers or has_code or has_paragraphs

    def _is_repo_url(self, url: str) -> bool:
        """Check if URL looks like a repository."""
        if not url:
            return False
        parsed = urlparse(url)
        return parsed.netloc in ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org")

    def _normalize_repo_url(self, url: str) -> str:
        """Normalize repository URL (remove .git suffix, fragments, etc)."""
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        parsed = urlparse(url)
        # Keep only scheme, netloc, and path (first two segments)
        path_parts = parsed.path.strip("/").split("/")[:2]
        return f"{parsed.scheme}://{parsed.netloc}/{'/'.join(path_parts)}"

    async def check_llms_txt(self, docs_url: str | None, repo_url: str | None) -> str | None:
        """Check for llms.txt or llms-full.txt at common locations."""
        urls_to_try = []

        if docs_url:
            base = docs_url.rstrip("/")
            urls_to_try.extend([f"{base}/llms-full.txt", f"{base}/llms.txt"])

        if repo_url and "github.com" in repo_url:
            # Try raw GitHub URLs
            parts = urlparse(repo_url).path.strip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[:2]
                for branch in ["main", "master"]:
                    urls_to_try.extend([
                        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/docs/llms-full.txt",
                        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/docs/llms.txt",
                        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/llms-full.txt",
                        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/llms.txt",
                    ])

        for url in urls_to_try:
            try:
                response = await self._get_with_retry(url, follow_redirects=True)
                if response.status_code == 200:
                    content = response.text
                    # Validate content is actual documentation, not HTML/JSON garbage
                    if len(content) > 100 and self._is_valid_llms_content(content):
                        console.print(f"[green]Found llms.txt at {url}[/green]")
                        return content
                    elif len(content) > 100:
                        console.print(
                            f"[yellow]Skipping {url} - content looks like HTML/JSON, not documentation[/yellow]"
                        )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # Retry exhausted, log and continue to next URL
                console.print(f"[yellow]Network error fetching {url}: {e}[/yellow]")
                continue
            except Exception:
                continue

        return None

    async def fetch_docs(
        self, metadata: ProjectMetadata, output_dir: Path
    ) -> tuple[DocSource, list[Path]]:
        """
        Fetch documentation for a package. Tries multiple sources in order:
        1. llms.txt (if available)
        2. GitHub/GitLab docs folder
        3. ReadTheDocs download
        4. PyPI description as fallback
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Try llms.txt first
        llms_content = await self.check_llms_txt(
            metadata.documentation_url, metadata.repository_url
        )
        if llms_content:
            llms_file = output_dir / "llms.txt"
            llms_file.write_text(llms_content)
            return DocSource.LLMS_TXT, [llms_file]

        # Try cloning docs from repo
        if metadata.repository_url:
            docs_files = await self._clone_docs(metadata.repository_url, output_dir)
            if docs_files:
                source = DocSource.GITHUB if "github" in metadata.repository_url else DocSource.GITLAB
                return source, docs_files

        # Try ReadTheDocs
        if metadata.documentation_url and "readthedocs" in metadata.documentation_url:
            rtd_files = await self._fetch_readthedocs(metadata, output_dir)
            if rtd_files:
                return DocSource.READTHEDOCS, rtd_files

        # Fallback to PyPI description - always create something useful
        desc_file = output_dir / "description.md"
        content_parts = [f"# {metadata.name}\n"]
        
        if metadata.summary:
            content_parts.append(f"\n{metadata.summary}\n")
        
        if metadata.keywords:
            content_parts.append(f"\n**Keywords**: {', '.join(metadata.keywords)}\n")
        
        if metadata.documentation_url:
            content_parts.append(f"\n**Documentation**: {metadata.documentation_url}\n")
        
        if metadata.repository_url:
            content_parts.append(f"\n**Repository**: {metadata.repository_url}\n")
        
        if metadata.author:
            content_parts.append(f"\n**Author**: {metadata.author}\n")
        
        content = "\n".join(content_parts)
        if len(content) > 50:  # Only if we have meaningful content
            desc_file.write_text(content)
            return DocSource.PYPI_DESCRIPTION, [desc_file]

        return DocSource.PYPI_DESCRIPTION, []

    async def _clone_docs(self, repo_url: str, output_dir: Path) -> list[Path]:
        """Clone just the docs folder from a repository using sparse checkout."""
        console.print(f"[blue]Cloning docs from {repo_url}...[/blue]")

        # Common docs folder names to try
        docs_folders = ["docs", "doc", "documentation", "docs/source"]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            try:
                # Initialize sparse checkout
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", repo_url, "repo"],
                    cwd=tmp_path,
                    capture_output=True,
                    timeout=60,
                    check=True,
                )

                repo_path = tmp_path / "repo"

                # Try each docs folder
                for folder in docs_folders:
                    subprocess.run(
                        ["git", "sparse-checkout", "set", folder],
                        cwd=repo_path,
                        capture_output=True,
                        timeout=30,
                    )

                    docs_path = repo_path / folder
                    if docs_path.exists() and any(docs_path.iterdir()):
                        # Copy docs to output
                        shutil.copytree(docs_path, output_dir / "docs", dirs_exist_ok=True)
                        console.print(f"[green]Found docs in {folder}/[/green]")
                        break

                # Also try to get README
                subprocess.run(
                    ["git", "sparse-checkout", "add", "README.md", "README.rst", "readme.md"],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=30,
                )

                for readme in ["README.md", "README.rst", "readme.md"]:
                    readme_path = repo_path / readme
                    if readme_path.exists():
                        shutil.copy(readme_path, output_dir / readme)
                        break

            except subprocess.TimeoutExpired:
                console.print(
                    f"[yellow]Warning: Git clone timed out for {repo_url}[/yellow]\n"
                    f"[dim]  Will fall back to PyPI description[/dim]"
                )
                return []
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode() if e.stderr else ""
                if "not found" in stderr.lower() or "404" in stderr:
                    console.print(
                        f"[yellow]Warning: Repository not found: {repo_url}[/yellow]\n"
                        f"[dim]  Will fall back to PyPI description[/dim]"
                    )
                elif "permission denied" in stderr.lower() or "authentication" in stderr.lower():
                    console.print(
                        f"[yellow]Warning: No access to repository: {repo_url}[/yellow]\n"
                        f"[dim]  Repository may be private. Will fall back to PyPI description[/dim]"
                    )
                else:
                    console.print(
                        f"[yellow]Warning: Could not clone {repo_url}[/yellow]\n"
                        f"[dim]  {stderr.strip() if stderr else 'Unknown git error'}[/dim]\n"
                        f"[dim]  Will fall back to PyPI description[/dim]"
                    )
                return []
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Unexpected error cloning {repo_url}: {e}[/yellow]\n"
                    f"[dim]  Will fall back to PyPI description[/dim]"
                )
                return []

        # Collect all doc files
        return self._collect_doc_files(output_dir)

    async def _fetch_readthedocs(self, metadata: ProjectMetadata, output_dir: Path) -> list[Path]:
        """Try to download docs from ReadTheDocs."""
        docs_url = metadata.documentation_url
        if not docs_url:
            return []

        # Parse project name from RTD URL
        match = re.search(r"([\w-]+)\.readthedocs", docs_url)
        if not match:
            return []

        project_name = match.group(1)
        console.print(f"[blue]Trying ReadTheDocs download for {project_name}...[/blue]")

        # Try downloading the zipfile of HTML docs
        download_urls = [
            f"https://{project_name}.readthedocs.io/_/downloads/en/stable/htmlzip/",
            f"https://{project_name}.readthedocs.io/_/downloads/en/latest/htmlzip/",
        ]

        for url in download_urls:
            try:
                response = await self._get_with_retry(url, follow_redirects=True)
                if response.status_code == 200:
                    zip_path = output_dir / "docs.zip"
                    zip_path.write_bytes(response.content)

                    # Unzip
                    import zipfile
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(output_dir / "html")
                    zip_path.unlink()

                    console.print("[green]Downloaded ReadTheDocs HTML[/green]")
                    return self._collect_doc_files(output_dir)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                console.print(f"[yellow]RTD download failed after retries: {e}[/yellow]")
                continue
            except Exception as e:
                console.print(f"[yellow]RTD download failed: {e}[/yellow]")
                continue

        return []

    def _collect_doc_files(self, directory: Path) -> list[Path]:
        """Collect all documentation files from a directory."""
        extensions = {".md", ".rst", ".txt", ".html"}
        files = []

        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))

        # Filter out some noise
        files = [
            f
            for f in files
            if not any(
                skip in str(f).lower()
                for skip in ["changelog", "changes", "history", "news", "license", "contributing", "code_of_conduct"]
            )
        ]

        # Limit number of files
        return sorted(files)[: settings.max_doc_files]
