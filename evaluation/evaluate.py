#!/usr/bin/env python3
"""
Evaluation script for docstore.

Runs all scenarios in sequence and outputs docstore results.
The agent will interleave Context7 MCP calls for comparison.

Usage:
    uv run python evaluation/evaluate.py
"""

import json
import subprocess
from pathlib import Path


def run_docstore_query(library: str, query: str) -> str:
    """Run a docstore query and return output."""
    try:
        result = subprocess.run(
            ["uv", "run", "docstore", "search", query, "--project", library, "-n", "3"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).parent.parent,
        )
        output = result.stdout.strip()
        if not output or "No results" in output:
            return "(no results)"
        return output
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return f"(error: {e})"


def main():
    scenarios_path = Path(__file__).parent / "scenarios.json"
    data = json.loads(scenarios_path.read_text())

    all_scenarios = data["easy_problems"] + data["hard_problems"]

    for scenario in all_scenarios:
        print(f"\n## {scenario['id']}: {scenario['name']}")
        print(f"Libraries: {', '.join(scenario['libraries'])}\n")

        for q in scenario["queries"]:
            lib = q["library"]
            query = q["query"]

            print(f"### [{lib}] {query}")
            print("\nDocstore:")
            print(run_docstore_query(lib, query))
            print()


if __name__ == "__main__":
    main()
