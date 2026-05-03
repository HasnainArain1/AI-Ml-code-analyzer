"""
schemas.py — Pydantic request/response models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Request ──────────────────────────────────────

class CodeReviewRequest(BaseModel):
    code: str


# ── Response ─────────────────────────────────────

class MetricsResponse(BaseModel):
    cyclomatic_complexity: int
    num_params: int
    num_lines: int
    has_docstring: int
    comment_ratio: float
    nesting_depth: int
    num_returns: int


class ReviewResponse(BaseModel):
    id: int
    func_name: str
    rating: str
    score: float
    metrics: MetricsResponse
    suggestions: str
    improved_code: str
    diff: str
    created_at: datetime

    class Config:
        from_attributes = True


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []


class ReviewHistoryItem(BaseModel):
    id: int
    func_name: str
    rating: str
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewDetailResponse(BaseModel):
    id: int
    code: str
    func_name: str
    rating: str
    score: float
    metrics: MetricsResponse
    suggestions: str
    improved_code: str
    diff: str
    created_at: datetime

    class Config:
        from_attributes = True
