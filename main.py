"""AI Code Review Agent – FastAPI Entry Point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.review import router
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s – %(message)s")

app = FastAPI(
    title="AI Code Review Agent",
    description="Automated code review using GPT-4o + AST static analysis. Detects bugs, security vulnerabilities, performance issues, and code quality problems with actionable fix suggestions.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "AI Code Review Agent",
        "version": "1.0.0",
        "capabilities": ["LLM-powered code review (GPT-4o)", "Python AST static analysis", "Cyclomatic complexity measurement", "Security vulnerability detection", "Git diff / PR review", "Automated test generation"],
        "supported_languages": ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C/C++"],
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
