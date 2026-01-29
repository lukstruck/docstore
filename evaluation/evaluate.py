#!/usr/bin/env python3
"""
Evaluation helper for docstore.

Designed to be used by an agent that will:
1. List scenarios with --list
2. Run individual queries with --query
3. Compare docstore output with Context7 output
4. Create a summary

Usage:
    uv run python evaluation/evaluate.py --list
    uv run python evaluation/evaluate.py --query "pydantic" "BaseModel field_validator"
    uv run python evaluation/evaluate.py --index "pydantic"
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def list_scenarios():
    """Print all scenarios and their queries."""
    scenarios_path = Path(__file__).parent / "scenarios.json"
    data = json.loads(scenarios_path.read_text())

    print("=== EVALUATION SCENARIOS ===\n")

    for category in ["easy_problems", "hard_problems"]:
        print(f"## {category.upper().replace('_', ' ')}\n")
        for scenario in data[category]:
            print(f"### {scenario['id']}: {scenario['name']}")
            print(f"Libraries: {', '.join(scenario['libraries'])}")
            print("Queries:")
            for q in scenario["queries"]:
                print(f"  - [{q['library']}] {q['query']}")
            print()


def run_query(library: str, query: str):
    """Run a docstore query and print results."""
    print(f"=== DOCSTORE QUERY ===")
    print(f"Library: {library}")
    print(f"Query: {query}")
    print()

    try:
        result = subprocess.run(
            ["uv", "run", "docstore", "search", query, "--project", library, "-n", "5"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).parent.parent,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("ERROR: Query timed out")
    except Exception as e:
        print(f"ERROR: {e}")


def index_library(library: str):
    """Index a library."""
    print(f"=== INDEXING {library} ===")

    try:
        result = subprocess.run(
            ["uv", "run", "docstore", "index", library],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(__file__).parent.parent,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("ERROR: Indexing timed out")
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Evaluation helper for docstore")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument("--query", nargs=2, metavar=("LIBRARY", "QUERY"), help="Run a query")
    parser.add_argument("--index", metavar="LIBRARY", help="Index a library")

    args = parser.parse_args()

    if args.list:
        list_scenarios()
    elif args.query:
        run_query(args.query[0], args.query[1])
    elif args.index:
        index_library(args.index)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
