# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a SWE-bench Pro GitHub Actions Hackathon project for automating task evaluation. The goal is to build a complete GitHub repository with a GitHub Actions workflow that:
1. Downloads a pre-configured Docker environment
2. Sets up the OpenLibrary repository for testing
3. Runs pre-verification tests (expecting them to fail)
4. Uses AI coding agents to generate fixes
5. Runs post-verification tests (expecting them to pass)
6. Generates required artifacts

## Task Details

- **Task ID**: `internetarchive__openlibrary-c4eebe6677acc4629cb541a98d5e91311444f5d4`
- **Repository**: OpenLibrary (Internet Archive)
- **Docker Image**: `manojva/openlibrary-python312:latest`
- **Problem**: Improve ISBN import logic by using local staged records instead of external API calls

## Key Commands

### Repository Setup
```bash
git reset --hard 84cc4ed5697b83a849e9106a09bfed501169cc20
git clean -fd
git checkout c4eebe6677acc4629cb541a98d5e91311444f5d4 -- openlibrary/tests/core/test_imports.py
```

### Running Tests
```bash
# Pre-verification tests (should fail before fix)
cd /testbed && python -m pytest openlibrary/tests/core/test_imports.py::TestImportItem::test_find_staged_or_pending -xvs

# All related tests (for validation)
cd /testbed && python -m pytest openlibrary/tests/core/test_imports.py -v
```

### Artifact Generation
```bash
# Generate patch of changes
git diff > /tmp/changes.patch

# Extract metrics from agent.log
python extract_metrics.py
```

## Architecture

### Core Components

1. **GitHub Actions Workflow** (`.github/workflows/swe-bench-eval.yml`)
   - Orchestrates the entire evaluation process
   - Uses Docker container with pre-configured environment
   - Handles artifact collection and upload

2. **AI Agent Runner** (`run_agent.py` or `run_claude.py`)
   - Interfaces with chosen AI API (Claude, Gemini, OpenAI, or Cursor)
   - Implements tool functions (read_file, write_file, edit_file, run_bash)
   - Logs all interactions to `agent.log` in JSONL format
   - Documents prompts used in `prompts.md`

3. **Metrics Extractor** (`extract_metrics.py`)
   - Parses `agent.log` to calculate token usage and costs
   - Verifies test success from post-verification logs
   - Generates `result.json` with evaluation metrics

## Task Implementation Requirements

The task requires implementing a `find_staged_or_pending` static method in `openlibrary/core/imports.py` that:
- Takes identifiers (list[str]) and sources (Iterable[str], defaults to STAGED_SOURCES)
- Constructs ia_id values in format `{source}:{identifier}`
- Returns ResultSet from import_item table with status 'staged' or 'pending'
- Must define STAGED_SOURCES tuple containing at minimum ('amazon', 'idb')

## Required Artifacts

All artifacts must be generated in `/tmp/`:
- `agent.log`: JSONL format with AI agent interactions
- `result.json`: Metrics including resolution status, duration, cost, tokens
- `pre_verification.log`: Test output before fix (should show failures)
- `post_verification.log`: Test output after fix (should show passes)
- `changes.patch`: Git diff of all changes made
- `prompts.md`: Documentation of all prompts used

## Artifact Formats

### agent.log (JSONL)
```json
{"timestamp": "ISO-8601", "type": "request|response|tool_use", "content": "..."}
```

### result.json
```json
{
  "resolved": boolean,
  "duration_seconds": number,
  "total_cost_usd": number,
  "tokens": {"input": number, "output": number, "cache_read": 0, "cache_write": 0},
  "tool_usage": {"read": number, "write": number, "edit": number, "bash": number}
}
```