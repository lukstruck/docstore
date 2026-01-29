# Docstore

Python documentation store with semantic search, ChromaDB backend, and HTTP/MCP APIs.

## Features

- **Smart PyPI lookup**: Automatically finds documentation from GitHub, GitLab, ReadTheDocs, or llms.txt
- **Multi-format support**: Handles Markdown, RST, and HTML documentation
- **Semantic search**: ChromaDB-powered vector search with metadata filtering
- **Project tagging**: Tag packages for organized filtering (e.g., `web`, `ml`, `testing`)
- **HTTP API**: RESTful API for integration with any service
- **MCP Server**: Direct Claude integration via Model Context Protocol
- **CLI**: Full command-line interface for manual operations

## Installation

```bash
# Clone and install
cd docstore
pip install -e .

# Install pandoc for better RST conversion (optional but recommended)
# Ubuntu/Debian:
sudo apt install pandoc
# macOS:
brew install pandoc
```

## Quick Start

### Index packages

```bash
# Single package
docstore index fastapi

# With tags
docstore index pydantic --tag validation --tag web

# From requirements.txt
docstore index-requirements requirements.txt --tag myproject

# Force reindex
docstore index httpx --force
```

### Search documentation

```bash
# Basic search
docstore search "how to create a router"

# Filter by project
docstore search "validation" --project pydantic

# Filter by tag
docstore search "async http" --tag web
```

### Manage projects

```bash
# List indexed projects
docstore list-projects

# Show statistics
docstore stats

# Delete a project
docstore delete fastapi
```

## HTTP API

Start the server:

```bash
docstore serve
# or
docstore serve --host 0.0.0.0 --port 8420
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/stats` | GET | Storage statistics |
| `/projects` | GET | List all indexed projects |
| `/projects/{name}` | GET | Get project info |
| `/projects/{name}` | DELETE | Delete a project |
| `/index` | POST | Index a package |
| `/index/requirements` | POST | Index from requirements.txt |
| `/search` | POST | Search documentation |
| `/update/{name}` | POST | Update to latest version |

### Example requests

```bash
# Index a package
curl -X POST http://localhost:8420/index \
  -H "Content-Type: application/json" \
  -d '{"package": "httpx", "tags": ["http", "async"]}'

# Search
curl -X POST http://localhost:8420/search \
  -H "Content-Type: application/json" \
  -d '{"query": "connection pooling", "n_results": 5}'

# Search with filters
curl -X POST http://localhost:8420/search \
  -H "Content-Type: application/json" \
  -d '{"query": "validation", "projects": ["pydantic"], "tags": ["web"]}'

# Index from requirements
curl -X POST http://localhost:8420/index/requirements \
  -H "Content-Type: application/json" \
  -d '{"requirements": "fastapi>=0.100\npydantic>=2.0", "tags": ["api"]}'
```

## MCP Server (Claude Integration)

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "docstore": {
      "command": "docstore-mcp",
      "env": {
        "DOCSTORE_DATA_DIR": "/path/to/data"
      }
    }
  }
}
```

Or run standalone:

```bash
docstore mcp
```

### Available MCP Tools

- `search_docs` - Search indexed documentation
- `list_indexed_projects` - List available packages
- `index_package` - Index a new package
- `get_stats` - Get storage statistics

## Configuration

Environment variables (prefix with `DOCSTORE_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Data storage directory |
| `CACHE_DIR` | `./cache` | Cache directory |
| `COLLECTION_NAME` | `python_docs` | ChromaDB collection name |
| `HOST` | `0.0.0.0` | HTTP server host |
| `PORT` | `8420` | HTTP server port |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `MAX_RETRIES` | `3` | Retry attempts for network failures |
| `RETRY_BACKOFF_BASE` | `1.0` | Initial retry delay (seconds) |
| `RETRY_BACKOFF_MAX` | `10.0` | Maximum retry delay (seconds) |
| `GITHUB_TOKEN` | `None` | GitHub API token (optional, for higher rate limits) |

Or create a `.env` file:

```env
DOCSTORE_DATA_DIR=/var/lib/docstore
DOCSTORE_PORT=8080
```

## Docker

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y git pandoc && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8420
CMD ["docstore", "serve"]
```

```yaml
# docker-compose.yml
services:
  docstore:
    build: .
    ports:
      - "8420:8420"
    volumes:
      - docstore-data:/app/data
    environment:
      - DOCSTORE_DATA_DIR=/app/data

volumes:
  docstore-data:
```

## How It Works

1. **Fetch**: Looks up package on PyPI, finds repo/docs URL
2. **Download**: Tries in order (with automatic retry on network failures):
   - `llms.txt` / `llms-full.txt` (validated to reject HTML/JSON garbage)
   - Git sparse checkout of `/docs` folder (falls back to GitHub API if git fails)
   - ReadTheDocs HTML download
   - PyPI description fallback
3. **Convert**: RST/HTML → Markdown (uses pandoc if available)
4. **Chunk**: Semantic splitting by headers, then by size
5. **Embed**: ChromaDB handles embedding via default model
6. **Store**: Persisted to disk with project/version/tag metadata

## Evaluation

The `evaluation/` directory contains test scenarios for comparing docstore performance:

```bash
# Run evaluation (outputs docstore results for all scenarios)
uv run python evaluation/evaluate.py
```

Scenarios are defined in `evaluation/scenarios.json` covering common Python libraries.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format src/
ruff check --fix src/
```

## License

MIT
