"""
AI Code Review Agent – LLM + AST static analysis for automated PR reviews.
Combines GPT-4o reasoning with cyclomatic complexity, security scanning, and style checks.
"""
import ast
import logging
import json
import re
import textwrap
from typing import Optional, List
from openai import OpenAI
from anthropic import Anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

REVIEW_SYSTEM_PROMPT = """You are a senior software engineer conducting a thorough code review.
Analyse the code for:
1. **Bugs & Logic Errors** – off-by-one errors, null pointer issues, race conditions
2. **Security Vulnerabilities** – SQL injection, XSS, hardcoded secrets, insecure deps
3. **Performance Issues** – O(n²) loops, unnecessary DB calls, memory leaks
4. **Code Quality** – DRY violations, naming conventions, complex functions
5. **Best Practices** – error handling, type hints, documentation

For each issue found, provide:
- Severity: CRITICAL | HIGH | MEDIUM | LOW | INFO
- Line range (if applicable)
- Clear description
- Specific fix with code example"""

SUMMARY_PROMPT = """Based on the code review findings, provide:
1. Overall quality score (0-100)
2. Executive summary (2-3 sentences)
3. Top 3 priority fixes
4. Positive aspects of the code
5. Estimated refactor effort: LOW | MEDIUM | HIGH

Issues found:
{issues}"""


class StaticAnalyser:
    """Python-specific AST-based static analysis."""

    @staticmethod
    def analyse_python(code: str) -> dict:
        issues = []
        metrics = {}
        try:
            tree = ast.parse(code)

            # Check for broad exception catches
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        issues.append({
                            "type": "broad_exception",
                            "severity": "MEDIUM",
                            "line": node.lineno,
                            "message": "Bare `except:` catches all exceptions. Use specific exception types.",
                        })
                    elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                        issues.append({
                            "type": "broad_exception",
                            "severity": "LOW",
                            "line": node.lineno,
                            "message": "Catching `Exception` is too broad. Consider catching specific exceptions.",
                        })

            # Check for dangerous builtins
            dangerous = {"eval", "exec", "compile", "__import__"}
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in dangerous:
                        issues.append({
                            "type": "dangerous_builtin",
                            "severity": "CRITICAL",
                            "line": node.lineno,
                            "message": f"Use of dangerous builtin `{node.func.id}` can lead to code injection.",
                        })

            # Check function complexity (number of branches)
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    branch_count = sum(
                        1 for n in ast.walk(node)
                        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.With))
                    )
                    complexity = branch_count + 1
                    functions.append({"name": node.name, "line": node.lineno, "complexity": complexity})
                    if complexity > settings.COMPLEXITY_THRESHOLD:
                        issues.append({
                            "type": "high_complexity",
                            "severity": "HIGH",
                            "line": node.lineno,
                            "message": f"Function `{node.name}` has cyclomatic complexity {complexity} (threshold: {settings.COMPLEXITY_THRESHOLD}). Consider refactoring.",
                        })

            # Check for hardcoded secrets
            secret_patterns = [
                (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded password"),
                (r'(?i)(api_key|apikey|secret|token)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key/secret"),
                (r'(?i)(aws_access|aws_secret)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded AWS credential"),
            ]
            for i, line in enumerate(code.splitlines(), 1):
                for pattern, msg in secret_patterns:
                    if re.search(pattern, line):
                        issues.append({
                            "type": "hardcoded_secret",
                            "severity": "CRITICAL",
                            "line": i,
                            "message": f"{msg} detected. Use environment variables instead.",
                        })

            # Metrics
            metrics = {
                "total_lines": len(code.splitlines()),
                "total_functions": len(functions),
                "avg_complexity": round(sum(f["complexity"] for f in functions) / max(len(functions), 1), 1),
                "functions": functions,
            }

        except SyntaxError as e:
            issues.append({"type": "syntax_error", "severity": "CRITICAL", "line": e.lineno, "message": f"Syntax error: {e.msg}"})
        except Exception as e:
            logger.error("Static analysis failed: %s", e)

        return {"issues": issues, "metrics": metrics}


class CodeReviewService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.static_analyser = StaticAnalyser()

    def review_code(self, code: str, language: str = "python", filename: str = "code.py", context: str = "") -> dict:
        # Step 1: Static analysis (for Python)
        static_results = {}
        if language.lower() == "python":
            static_results = self.static_analyser.analyse_python(code)

        # Step 2: LLM review
        lang_info = f"Language: {language}\nFilename: {filename}"
        if context:
            lang_info += f"\nContext: {context}"
        code_preview = code[:8000]  # Limit to 8K chars
        messages = [
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": f"{lang_info}\n\n```{language}\n{code_preview}\n```\n\nProvide detailed code review in JSON format:\n{{\"issues\": [{{\"severity\": \"...\", \"category\": \"...\", \"line_range\": \"...\", \"description\": \"...\", \"suggestion\": \"...\"}}], \"positive_aspects\": [\"...\"]}}"},
        ]

        try:
            resp = self.openai_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=3000,
            )
            llm_review = json.loads(resp.choices[0].message.content)
        except Exception as exc:
            logger.error("LLM review failed: %s", exc)
            llm_review = {"issues": [], "positive_aspects": [], "error": str(exc)}

        # Step 3: Summary
        all_issues_text = json.dumps(llm_review.get("issues", []) + static_results.get("issues", []), indent=2)
        summary_resp = self.openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": SUMMARY_PROMPT.format(issues=all_issues_text[:3000])}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        summary = json.loads(summary_resp.choices[0].message.content)

        # Combine results
        all_issues = llm_review.get("issues", []) + static_results.get("issues", [])
        critical = [i for i in all_issues if i.get("severity") == "CRITICAL"]
        high = [i for i in all_issues if i.get("severity") == "HIGH"]

        return {
            "filename": filename,
            "language": language,
            "summary": summary,
            "llm_review": llm_review,
            "static_analysis": static_results,
            "total_issues": len(all_issues),
            "critical_count": len(critical),
            "high_count": len(high),
            "positive_aspects": llm_review.get("positive_aspects", []),
        }

    def review_diff(self, diff: str, context: str = "") -> dict:
        """Review a git diff / pull request."""
        prompt = f"""Review this git diff for a pull request. Focus on:
- New bugs introduced
- Security issues in added code
- Correctness of logic changes
- Missing test coverage indicators

{"Context: " + context if context else ""}

Diff:
```diff
{diff[:6000]}
```

Return JSON: {{"pr_summary": "...", "issues": [...], "approval_recommendation": "APPROVE|REQUEST_CHANGES|COMMENT", "review_confidence": 0-100}}"""

        resp = self.openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)

    def suggest_tests(self, code: str, language: str = "python") -> dict:
        """Generate test suggestions for the given code."""
        prompt = f"""Generate comprehensive unit tests for this {language} code.
Include:
- Happy path tests
- Edge cases
- Error/exception tests
- Boundary condition tests

Code:
```{language}
{code[:4000]}
```

Return JSON: {{"test_framework": "...", "test_code": "...", "test_cases": [{{"name": "...", "description": "...", "test_type": "..."}}]}}"""

        resp = self.openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(resp.choices[0].message.content)


_service: Optional[CodeReviewService] = None
def get_review_service() -> CodeReviewService:
    global _service
    if _service is None:
        _service = CodeReviewService()
    return _service
