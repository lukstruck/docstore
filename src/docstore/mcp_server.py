"""MCP server for docstore - enables Claude to search Python documentation."""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)
from pydantic import BaseModel

from .indexer import DocIndexer
from .models import IndexRequest
from .store import DocStore


class MCPDocStore:
    """MCP server wrapper for docstore."""

    def __init__(self):
        self.store = DocStore()
        self.indexer = DocIndexer(self.store)
        self.server = Server("docstore")

        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="search_docs",
                        description="Search Python package documentation. Returns relevant chunks with context.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query - what you want to find in the documentation",
                                },
                                "n_results": {
                                    "type": "integer",
                                    "description": "Number of results to return (default: 5)",
                                    "default": 5,
                                },
                                "projects": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter to specific projects (optional)",
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter by tags (optional)",
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="list_indexed_projects",
                        description="List all Python packages that have been indexed and are available for search.",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                    Tool(
                        name="index_package",
                        description="Index documentation for a Python package from PyPI. Downloads and processes docs automatically.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "package": {
                                    "type": "string",
                                    "description": "PyPI package name (e.g., 'fastapi', 'pydantic')",
                                },
                                "version": {
                                    "type": "string",
                                    "description": "Specific version to index (optional, defaults to latest)",
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Tags to apply to this package for filtering",
                                },
                                "force": {
                                    "type": "boolean",
                                    "description": "Force reindex even if already indexed",
                                    "default": False,
                                },
                            },
                            "required": ["package"],
                        },
                    ),
                    Tool(
                        name="get_stats",
                        description="Get statistics about the documentation store.",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            try:
                if name == "search_docs":
                    return await self._search_docs(arguments)
                elif name == "list_indexed_projects":
                    return await self._list_projects()
                elif name == "index_package":
                    return await self._index_package(arguments)
                elif name == "get_stats":
                    return await self._get_stats()
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )

    async def _search_docs(self, args: dict[str, Any]) -> CallToolResult:
        """Handle search_docs tool call."""
        results = self.store.search(
            query=args["query"],
            n_results=args.get("n_results", 5),
            projects=args.get("projects"),
            tags=args.get("tags"),
        )

        if not results:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"No results found for '{args['query']}'. Try indexing more packages with index_package.",
                    )
                ]
            )

        # Format results nicely
        output_parts = [f"Found {len(results)} results for '{args['query']}':\n"]

        for i, result in enumerate(results, 1):
            output_parts.append(f"\n--- Result {i} ({result.project} v{result.version}) ---")
            if result.title:
                output_parts.append(f"Title: {result.title}")
            output_parts.append(f"Source: {result.source_file}")
            output_parts.append(f"Score: {result.score:.3f}")
            output_parts.append(f"\n{result.content}\n")

        return CallToolResult(
            content=[TextContent(type="text", text="\n".join(output_parts))]
        )

    async def _list_projects(self) -> CallToolResult:
        """Handle list_indexed_projects tool call."""
        projects = self.store.list_projects()

        if not projects:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="No projects indexed yet. Use index_package to add documentation.",
                    )
                ]
            )

        output_parts = [f"Indexed {len(projects)} projects:\n"]
        for p in sorted(projects, key=lambda x: x.name):
            tags_str = f" [{', '.join(p.tags)}]" if p.tags else ""
            output_parts.append(
                f"- {p.name} v{p.version}: {p.chunk_count} chunks ({p.source.value}){tags_str}"
            )

        return CallToolResult(
            content=[TextContent(type="text", text="\n".join(output_parts))]
        )

    async def _index_package(self, args: dict[str, Any]) -> CallToolResult:
        """Handle index_package tool call."""
        request = IndexRequest(
            package=args["package"],
            version=args.get("version"),
            tags=args.get("tags", []),
            force=args.get("force", False),
        )

        result = await self.indexer.index_package(request)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Successfully indexed {result.name} v{result.version}:\n"
                    f"- Source: {result.source.value}\n"
                    f"- Chunks: {result.chunk_count}\n"
                    f"- Tags: {', '.join(result.tags) if result.tags else 'none'}",
                )
            ]
        )

    async def _get_stats(self) -> CallToolResult:
        """Handle get_stats tool call."""
        stats = self.store.get_stats()

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Docstore Statistics:\n"
                    f"- Total chunks: {stats['total_chunks']}\n"
                    f"- Total projects: {stats['total_projects']}\n",
                )
            ]
        )

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


def run():
    """Entry point for MCP server."""
    server = MCPDocStore()
    asyncio.run(server.run())


if __name__ == "__main__":
    run()
