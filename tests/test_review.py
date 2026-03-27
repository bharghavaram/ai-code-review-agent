"""Tests for AI Code Review Agent."""
import pytest
from app.services.review_service import StaticAnalyser
from app.core.config import settings

def test_settings():
    assert settings.COMPLEXITY_THRESHOLD == 10
    assert settings.SECURITY_SCAN_ENABLED is True

def test_static_analyse_clean_code():
    analyser = StaticAnalyser()
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    result = analyser.analyse_python(code)
    assert "issues" in result
    assert "metrics" in result
    assert result["metrics"]["total_functions"] == 1

def test_static_analyse_detects_bare_except():
    analyser = StaticAnalyser()
    code = "try:\n    x = 1/0\nexcept:\n    pass\n"
    result = analyser.analyse_python(code)
    types = [i["type"] for i in result["issues"]]
    assert "broad_exception" in types

def test_static_analyse_detects_eval():
    analyser = StaticAnalyser()
    code = "user_input = 'print(1)'\neval(user_input)\n"
    result = analyser.analyse_python(code)
    types = [i["type"] for i in result["issues"]]
    assert "dangerous_builtin" in types

def test_static_analyse_hardcoded_secret():
    analyser = StaticAnalyser()
    code = 'api_key = "sk-abcdefghijklmnop"\n'
    result = analyser.analyse_python(code)
    types = [i["type"] for i in result["issues"]]
    assert "hardcoded_secret" in types

def test_static_analyse_syntax_error():
    analyser = StaticAnalyser()
    code = "def broken(:\n    pass"
    result = analyser.analyse_python(code)
    types = [i["type"] for i in result["issues"]]
    assert "syntax_error" in types

def test_severity_levels():
    valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
    analyser = StaticAnalyser()
    code = "eval('x')\ntry:\n    pass\nexcept:\n    pass\n"
    result = analyser.analyse_python(code)
    for issue in result["issues"]:
        assert issue["severity"] in valid_severities

@pytest.mark.asyncio
async def test_api_health():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/api/v1/review/health")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_api_review_empty_code():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.post("/api/v1/review/code", json={"code": "", "language": "python"})
    assert resp.status_code == 400
