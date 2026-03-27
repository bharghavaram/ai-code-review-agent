> **📅 Project Period:** Jul 2024 – Aug 2024 &nbsp;|&nbsp; **Status:** Completed &nbsp;|&nbsp; **Author:** [Bharghava Ram Vemuri](https://github.com/bharghavaram)

# AI Code Review Agent

> Automated code review using GPT-4o + AST static analysis for production codebases

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/GPT--4o-Reviewer-purple)](https://openai.com)

## Overview

An automated code review system that combines **GPT-4o LLM reasoning** with **Python AST static analysis** to detect bugs, security vulnerabilities, performance issues, and code quality problems — with actionable fix suggestions and test generation.

## What It Reviews

| Category | Examples |
|----------|----------|
| **Bugs** | Off-by-one errors, null references, race conditions |
| **Security** | SQL injection, hardcoded secrets, dangerous builtins (`eval`, `exec`) |
| **Performance** | O(n²) loops, N+1 queries, memory leaks |
| **Complexity** | Cyclomatic complexity > threshold, deeply nested logic |
| **Style** | DRY violations, missing type hints, poor naming |

## Architecture

```
Code/Diff Input
     ↓
AST Static Analysis (Python) → Syntax errors, bare excepts, dangerous builtins, secrets
     ↓
GPT-4o LLM Review → Bugs, security, performance, logic issues
     ↓
Summary Generator → Quality score, priority fixes, effort estimate
     ↓
Test Generator → Unit test suite for reviewed code
```

## Quick Start

```bash
git clone https://github.com/bharghavaram/ai-code-review-agent
cd ai-code-review-agent
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/review/code` | Full code review |
| POST | `/api/v1/review/diff` | Git diff / PR review |
| POST | `/api/v1/review/suggest-tests` | Generate unit tests |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/review/code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def login(user, pwd):\n    query = f\"SELECT * FROM users WHERE pwd=\\'{pwd}\\'\"\n    eval(query)",
    "language": "python",
    "filename": "auth.py"
  }'
```

### Response includes

- **Quality score** (0–100)
- **Issues by severity** (CRITICAL → INFO)
- **Static analysis** (AST-based)
- **Positive aspects** of the code
- **Refactor effort estimate**
