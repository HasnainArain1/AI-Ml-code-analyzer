"""
routers/history.py — Review history endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import ReviewHistory
from app.schemas import ReviewHistoryItem, ReviewDetailResponse, MetricsResponse
from app.differ import generate_diff

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=List[ReviewHistoryItem])
def list_reviews(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all past reviews, newest first."""
    reviews = (
        db.query(ReviewHistory)
        .order_by(ReviewHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return reviews


@router.get("/history/{review_id}", response_model=ReviewDetailResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a single review with full details."""
    review = db.query(ReviewHistory).filter(ReviewHistory.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Regenerate diff
    diff = generate_diff(review.code, review.improved_code or review.code)

    return ReviewDetailResponse(
        id=review.id,
        code=review.code,
        func_name=review.func_name,
        rating=review.rating,
        score=review.score,
        metrics=MetricsResponse(
            cyclomatic_complexity=review.cyclomatic_complexity,
            num_params=review.num_params,
            num_lines=review.num_lines,
            has_docstring=review.has_docstring,
            comment_ratio=review.comment_ratio,
            nesting_depth=review.nesting_depth,
            num_returns=review.num_returns,
        ),
        suggestions=review.suggestions or "",
        improved_code=review.improved_code or "",
        diff=diff,
        created_at=review.created_at,
    )


@router.delete("/history/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """Delete a review."""
    review = db.query(ReviewHistory).filter(ReviewHistory.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return {"message": "Review deleted", "id": review_id}
