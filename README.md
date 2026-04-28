# Code Review Agent

LLM-powered automated code review agent with multi-agent pipeline architecture. Automatically reviews Pull Requests for bugs, code quality, and security issues, and posts review comments directly to GitHub.

## Features

- **Multi-Agent Pipeline** — Three specialized LLM agents (Bug Hunter, Code Quality, Security) review code in parallel, powered by LangGraph
- **Architecture-Aware** — Scans project directory structure and analyzes file dependencies via AST to provide contextual reviews
- **GitHub Integration** — Runs as a GitHub Action, fetches PR diffs, and posts inline review comments + summary automatically
- **Team Skill Rules** — Load custom team review rules from `team-rules-skill/SKILL.md` and inject them into all agents
- **Local Mode** — Run reviews locally via CLI with `--diff`, `--diff-file`, or `--git` flags
- **Multi-Language Support** — Classifies files as backend, frontend, test, or config; adaptable to Python, TypeScript, Go, Java, Rust, and more

## Architecture

```
┌─────────────┐
│  PR Diff    │
└──────┬──────┘
       ▼
┌─────────────┐     ┌──────────────────┐
│ Preprocess  │────▶│   Architecture   │
│ (split by   │     │ (dir tree + AST) │
│  file/hunk) │     └────────┬─────────┘
└─────────────┘              │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌──────────┐  ┌───────────┐  ┌───────────┐
       │Bug Hunter│  │  Quality  │  │ Security  │
       └────┬─────┘  └─────┬─────┘  └─────┬─────┘
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    ┌─────────────┐
                    │ Aggregator  │
                    │ (dedup +    │
                    │  prioritize)│
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  GitHub     │
                    │  Comments   │
                    └─────────────┘
```

## Quick Start

### Prerequisites

- Python >= 3.11
- DeepSeek API key ([get one here](https://platform.deepseek.com))
- GitHub token (for PR integration)

### Installation

```bash
git clone <repo-url>
cd code-review-agent
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
GITHUB_TOKEN=your_github_token_here
```

### Local Usage

```bash
# Review uncommitted changes
python run_local.py --git

# Review from a diff file
python run_local.py --diff-file path/to/changes.diff

# Review from a raw diff string
python run_local.py --diff "diff --git a/foo.py b/foo.py ..."

# Specify project root for architecture analysis
python run_local.py --git --project-root /path/to/project
```

### GitHub Action

Add `.github/workflows/code_review.yml` to your repository. The workflow triggers on `pull_request` events (opened and synchronized) and automatically posts review results.

Required secrets:
- `GITHUB_TOKEN` — provided automatically by GitHub Actions
- `DEEPSEEK_API_KEY` — your DeepSeek API key

## Team Rules (SKILL)

Place team-specific review rules in `team-rules-skill/SKILL.md` with YAML frontmatter:

```markdown
---
name: my-team-rules
description: Team-specific code review rules
---

## Additional Checks
- All public functions must have docstrings
- Error handling must cover all edge cases

## Forbidden
- No hardcoded credentials
- No unsafe random number generation
```

The pipeline automatically loads this file and injects it into every agent's system prompt.

## Project Structure

```
src/
├── pipeline.py          # LangGraph review pipeline (DAG orchestration)
├── models.py            # Pydantic data models (Issue, DiffChunk, ReviewState)
├── llm_client.py        # DeepSeek LLM client (langchain-openai compatible)
├── preprocess.py        # Diff parsing and chunking
├── architect.py         # Directory scanning + AST dependency analysis
├── aggregator.py        # Issue deduplication, merging, prioritization
├── formatter.py         # Markdown review comment formatting
├── github_client.py     # GitHub API client (PR diff, comments, reviews)
├── skill_loader.py      # Team SKILL.md loader with YAML frontmatter parsing
└── agents/
    ├── base.py          # Abstract base agent with LLM review loop
    ├── bug_hunter.py    # Bug detection agent
    ├── quality.py       # Code quality agent
    └── security.py      # Security vulnerability agent

tests/                   # Test suite (pytest)
team-rules-skill/        # Example team review rules
```

## How It Works

1. **Preprocess** — Parses the git diff, splits it by file and hunk into `DiffChunk` objects
2. **Architecture** — Scans the project directory tree and runs AST analysis on changed Python files to extract imports and defined symbols
3. **Parallel Review** — Three agents run concurrently, each calling the LLM with a specialized system prompt:
   - **Bug Hunter**: null checks, boundary conditions, exception handling, race conditions, logic errors
   - **Code Quality**: code duplication, function complexity, naming, coupling, SOLID violations
   - **Security**: SQL injection, XSS, hardcoded credentials, missing auth, insecure deserialization
4. **Aggregation** — Deduplicates issues by (file, line, type), keeps the highest-confidence version, and sorts by severity
5. **Output** — Formats results as Markdown and posts inline comments (high/medium severity) plus a summary comment on the PR

## License

MIT
