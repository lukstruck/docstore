"""Configuration settings for docstore."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(env_prefix="DOCSTORE_", env_file=".env")

    # Storage paths
    data_dir: Path = Path("./data")
    cache_dir: Path = Path("./cache")

    # ChromaDB settings
    chroma_persist_dir: Path | None = None  # None = use data_dir/chroma
    collection_name: str = "python_docs"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8420
    mcp_port: int = 8421

    # Chunking settings
    chunk_size: int = 1000  # characters
    chunk_overlap: int = 200

    # Fetching settings
    request_timeout: float = 30.0
    max_doc_files: int = 500  # Max files to process per project

    # Retry settings for transient network failures
    max_retries: int = 3
    retry_backoff_base: float = 1.0  # Initial wait time in seconds
    retry_backoff_max: float = 10.0  # Maximum wait time between retries

    # GitHub API settings (optional, for higher rate limits)
    github_token: str | None = None

    @property
    def chroma_path(self) -> Path:
        return self.chroma_persist_dir or self.data_dir / "chroma"

    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)


settings = Settings()
