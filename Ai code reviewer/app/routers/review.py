"""
routers/review.py — POST /api/review  +  POST /api/validate endpoints
"""

import ast
import logging
import textwrap
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import ReviewHistory
from app.schemas import (
    CodeReviewRequest,
    ReviewResponse,
    MetricsResponse,
    ValidateResponse,
)
from app.metrics import extract_metrics, extract_func_name
from app.predictor import predict
from app.groq_client import get_suggestions
from app.differ import generate_diff

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["review"])


# ── Shared validator (used by both endpoints) ────────────
def validate_python_code(code: str) -> list[str]:
    """
    Validate that `code` is syntactically correct Python containing
    at least one function definition.  Returns a list of human-readable
    error strings (empty list == valid).
    """
    errors: list[str] = []

    if not code or not code.strip():
        errors.append("Code cannot be empty.")
        return errors

    code = code.strip()

    # 1. Syntax check
    try:
        ast.parse(textwrap.dedent(code))
    except SyntaxError as exc:
        msg = f"SyntaxError on line {exc.lineno}: {exc.msg}"
        if exc.text:
            msg += f"  →  {exc.text.strip()}"
        errors.append(msg)
        return errors          # no point continuing

    # 2. Must contain a function
    if "def " not in code:
        errors.append("Code must contain at least one Python function (def …).")
        return errors

    # 3. Metrics extraction (AST + Radon) — catches deeper parse issues
    metrics = extract_metrics(code)
    if metrics is None:
        errors.append(
            "Could not fully parse the code.  "
            "Make sure it contains a valid Python function."
        )

    return errors


# ═══════════════════════════════════════════════════
# POST /api/validate   (Debug tab)
# ═══════════════════════════════════════════════════

@router.post("/validate", response_model=ValidateResponse)
def validate_code(request: CodeReviewRequest):
    """
    Validate code only — no analysis, no DB save.
    Returns {valid: true/false, errors: [...]}.
    """
    errors = validate_python_code(request.code)
    return ValidateResponse(valid=len(errors) == 0, errors=errors)


# ═══════════════════════════════════════════════════
# POST /api/review   (Analyze tab)
# ═══════════════════════════════════════════════════

@router.post("/review", response_model=ReviewResponse)
def review_code(request: CodeReviewRequest, db: Session = Depends(get_db)):
    """
    Full code review pipeline:
    0. Validate (shared validator)
    1. Extract metrics (AST + Radon)
    2. Predict rating (Random Forest)
    3. Get AI suggestions (Groq)
    4. Generate diff (difflib)
    5. Save to database
    6. Return complete review
    """
    code = request.code.strip()

    # 0. Shared validation
    errors = validate_python_code(code)
    if errors:
        raise HTTPException(status_code=400, detail=errors[0])

    try:
        # 1. Extract function name
        func_name = extract_func_name(code)
        logger.info(f"Extracted func_name: {func_name}")

        # 2. Extract metrics
        metrics = extract_metrics(code)
        if metrics is None:
            raise HTTPException(
                status_code=400,
                detail="Could not parse the code. Please ensure it's valid Python."
            )
        logger.info(f"Metrics: {metrics}")

        # 3. Predict rating
        label, confidence, score = predict(metrics)
        logger.info(f"Prediction: {label} ({confidence:.2f}), score={score}")

        # 4. Get AI suggestions + improved code
        suggestions, improved_code = get_suggestions(code, metrics, label, score)
        logger.info(f"Suggestions length: {len(suggestions)}, improved code length: {len(improved_code)}")

        # 5. Generate diff
        diff = generate_diff(code, improved_code)

        # 6. Save to database
        review = ReviewHistory(
            code=code,
            func_name=func_name,
            rating=label,
            score=score,
            cyclomatic_complexity=metrics["cyclomatic_complexity"],
            num_params=metrics["num_params"],
            num_lines=metrics["num_lines"],
            has_docstring=metrics["has_docstring"],
            comment_ratio=metrics["comment_ratio"],
            nesting_depth=metrics["nesting_depth"],
            num_returns=metrics["num_returns"],
            suggestions=suggestions,
            improved_code=improved_code,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        logger.info(f"Saved review id={review.id}")

        # 7. Return response
        return ReviewResponse(
            id=review.id,
            func_name=func_name,
            rating=label,
            score=score,
            metrics=MetricsResponse(**metrics),
            suggestions=suggestions,
            improved_code=improved_code,
            diff=diff,
            created_at=review.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review pipeline failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")
