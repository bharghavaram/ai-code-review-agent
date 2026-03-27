"""AI Code Review Agent – API routes."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.services.review_service import CodeReviewService, get_review_service

router = APIRouter(prefix="/review", tags=["Code Review"])

class ReviewRequest(BaseModel):
    code: str
    language: str = "python"
    filename: str = "code.py"
    context: Optional[str] = ""

class DiffRequest(BaseModel):
    diff: str
    context: Optional[str] = ""

class TestSuggestionRequest(BaseModel):
    code: str
    language: str = "python"

@router.post("/code")
async def review_code(req: ReviewRequest, svc: CodeReviewService = Depends(get_review_service)):
    if not req.code.strip():
        raise HTTPException(400, "code cannot be empty")
    return svc.review_code(req.code, req.language, req.filename, req.context)

@router.post("/diff")
async def review_diff(req: DiffRequest, svc: CodeReviewService = Depends(get_review_service)):
    if not req.diff.strip():
        raise HTTPException(400, "diff cannot be empty")
    return svc.review_diff(req.diff, req.context)

@router.post("/suggest-tests")
async def suggest_tests(req: TestSuggestionRequest, svc: CodeReviewService = Depends(get_review_service)):
    if not req.code.strip():
        raise HTTPException(400, "code cannot be empty")
    return svc.suggest_tests(req.code, req.language)

@router.get("/health")
async def health():
    return {"status": "ok", "service": "AI Code Review Agent – LLM + AST Static Analysis"}
