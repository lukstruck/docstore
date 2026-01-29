#!/usr/bin/env python3
"""
Evaluate docstore on predefined scenarios.

Runs queries from scenarios.json against docstore CLI,
measures response time, and checks for expected APIs in results.

Usage:
    uv run python evaluation/evaluate.py
    uv run python evaluation/evaluate.py --index-first  # Index libraries before testing
"""

import argparse
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class QueryResult:
    """Result of a single query."""

    query_id: str
    query: str
    library: str
    found: bool
    response_time_ms: float
    result_count: int
    expected_apis: list[str]
    found_apis: list[str]  # Which expected APIs were found
    raw_output: str


@dataclass
class ScenarioResult:
    """Aggregated results for a scenario."""

    scenario_id: str
    scenario_name: str
    queries: list[QueryResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Percentage of queries that found expected APIs."""
        if not self.queries:
            return 0.0
        found_count = sum(1 for q in self.queries if q.found_apis)
        return found_count / len(self.queries) * 100

    @property
    def api_coverage(self) -> float:
        """Percentage of expected APIs found across all queries."""
        total_expected = sum(len(q.expected_apis) for q in self.queries)
        total_found = sum(len(q.found_apis) for q in self.queries)
        if total_expected == 0:
            return 0.0
        return total_found / total_expected * 100

    @property
    def avg_response_time(self) -> float:
        """Average response time in ms."""
        if not self.queries:
            return 0.0
        return sum(q.response_time_ms for q in self.queries) / len(self.queries)


class Evaluator:
    """Evaluates docstore against predefined scenarios."""

    def __init__(self, scenarios_path: Path):
        self.scenarios = json.loads(scenarios_path.read_text())
        self.results: list[ScenarioResult] = []

    def run_docstore_query(self, query: str, library: str, expected_apis: list[str]) -> QueryResult:
        """Run a query via docstore CLI."""
        start = time.perf_counter()
        try:
            result = subprocess.run(
                ["uv", "run", "docstore", "search", query, "--project", library, "-n", "10"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=Path(__file__).parent.parent,
            )
            elapsed = (time.perf_counter() - start) * 1000
            output = result.stdout + result.stderr

            # Parse output for results
            found = "No results found" not in output and result.returncode == 0
            result_count = output.count("Score:")  # Count result entries

            # Check which expected APIs were found in the output
            found_apis = [api for api in expected_apis if api.lower() in output.lower()]

            return QueryResult(
                query_id=f"{library}:{query[:30]}",
                query=query,
                library=library,
                found=found,
                response_time_ms=elapsed,
                result_count=result_count,
                expected_apis=expected_apis,
                found_apis=found_apis,
                raw_output=output[:2000],  # Truncate for report
            )
        except subprocess.TimeoutExpired:
            elapsed = (time.perf_counter() - start) * 1000
            return QueryResult(
                query_id=f"{library}:{query[:30]}",
                query=query,
                library=library,
                found=False,
                response_time_ms=elapsed,
                result_count=0,
                expected_apis=expected_apis,
                found_apis=[],
                raw_output="TIMEOUT",
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return QueryResult(
                query_id=f"{library}:{query[:30]}",
                query=query,
                library=library,
                found=False,
                response_time_ms=elapsed,
                result_count=0,
                expected_apis=expected_apis,
                found_apis=[],
                raw_output=f"ERROR: {e}",
            )

    def index_library(self, library: str) -> bool:
        """Index a library if not already indexed."""
        print(f"  Indexing {library}...")
        try:
            result = subprocess.run(
                ["uv", "run", "docstore", "index", library],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=Path(__file__).parent.parent,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"    Failed to index {library}: {e}")
            return False

    def run_scenario(self, scenario: dict, index_first: bool = False) -> ScenarioResult:
        """Run all queries for a scenario."""
        result = ScenarioResult(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
        )

        # Index libraries if requested
        if index_first:
            for library in scenario["libraries"]:
                self.index_library(library)

        # Run queries
        for query_spec in scenario["queries"]:
            query_result = self.run_docstore_query(
                query=query_spec["query"],
                library=query_spec["library"],
                expected_apis=query_spec["expected_apis"],
            )
            result.queries.append(query_result)

        return result

    def run_all(self, index_first: bool = False) -> None:
        """Run all scenarios."""
        all_scenarios = self.scenarios["easy_problems"] + self.scenarios["hard_problems"]

        for scenario in all_scenarios:
            print(f"\nRunning scenario: {scenario['name']}")
            result = self.run_scenario(scenario, index_first=index_first)
            self.results.append(result)

            # Print quick summary
            print(f"  Success rate: {result.success_rate:.1f}%")
            print(f"  API coverage: {result.api_coverage:.1f}%")
            print(f"  Avg response: {result.avg_response_time:.0f}ms")

    def generate_report(self) -> str:
        """Generate markdown comparison report."""
        lines = ["# Docstore Evaluation Report", ""]

        # Summary
        lines.append("## Summary")
        lines.append("")
        total_queries = sum(len(r.queries) for r in self.results)
        total_found = sum(len(q.found_apis) for r in self.results for q in r.queries)
        total_expected = sum(len(q.expected_apis) for r in self.results for q in r.queries)
        avg_time = sum(r.avg_response_time for r in self.results) / len(self.results) if self.results else 0

        lines.append(f"- **Total queries**: {total_queries}")
        lines.append(f"- **Overall API coverage**: {total_found}/{total_expected} ({total_found/total_expected*100:.1f}%)" if total_expected else "- **Overall API coverage**: N/A")
        lines.append(f"- **Average response time**: {avg_time:.0f}ms")
        lines.append("")

        # Results by scenario
        lines.append("## Results by Scenario")
        lines.append("")
        lines.append("| Scenario | Success Rate | API Coverage | Avg Time |")
        lines.append("|----------|-------------|--------------|----------|")

        for result in self.results:
            lines.append(
                f"| {result.scenario_name} | {result.success_rate:.1f}% | {result.api_coverage:.1f}% | {result.avg_response_time:.0f}ms |"
            )

        lines.append("")

        # Detailed results
        lines.append("## Detailed Results")
        lines.append("")

        for result in self.results:
            lines.append(f"### {result.scenario_name}")
            lines.append("")

            for query in result.queries:
                status = "PASS" if query.found_apis else "FAIL"
                lines.append(f"**[{status}]** `{query.library}`: {query.query}")
                lines.append(f"- Expected: {', '.join(query.expected_apis)}")
                lines.append(f"- Found: {', '.join(query.found_apis) if query.found_apis else 'None'}")
                lines.append(f"- Time: {query.response_time_ms:.0f}ms, Results: {query.result_count}")
                lines.append("")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate docstore on predefined scenarios")
    parser.add_argument(
        "--index-first",
        action="store_true",
        help="Index libraries before running queries",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "results.md",
        help="Output file for report",
    )
    args = parser.parse_args()

    scenarios_path = Path(__file__).parent / "scenarios.json"
    evaluator = Evaluator(scenarios_path)

    print("Starting evaluation...")
    evaluator.run_all(index_first=args.index_first)

    report = evaluator.generate_report()
    args.output.write_text(report)
    print(f"\nReport written to: {args.output}")


if __name__ == "__main__":
    main()
