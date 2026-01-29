# Implementation Plan: Improve Docstore Reliability + Add Evaluation Framework

## Overview

Based on the evaluation results (docstore: 3.2/5 vs Context7: 4.5/5), implement improvements to address key failure modes and create an automated evaluation framework.

## Tasks

### Part 1: Docstore Improvements

- [x] 1.1 Add tenacity dependency to pyproject.toml
- [x] 1.2 Add retry and GitHub settings to config.py
- [x] 1.3 Add llms.txt content validation (_is_valid_llms_content method)
- [x] 1.4 Add retry logic with tenacity decorator
- [x] 1.5 Add GitHub API fallback for docs fetching

### Part 2: Evaluation Framework

- [x] 2.1 Create evaluation/scenarios.json with test queries
- [x] 2.2 Create evaluation/evaluate.py script

## Current Status

All tasks completed! Implementation includes:

1. **llms.txt validation** - Rejects HTML, JSON, and JavaScript garbage
2. **Retry logic** - Uses tenacity for exponential backoff on network failures
3. **GitHub API fallback** - Falls back to Contents API when git clone fails
4. **Evaluation framework** - Automated testing against 10 scenarios (5 easy, 5 hard)

## Verification

Run the evaluation:
```bash
uv run python evaluation/evaluate.py --index-first
```
