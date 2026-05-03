"""
db_models.py — SQLAlchemy ORM models
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


class ReviewHistory(Base):
    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(Text, nullable=False)
    func_name = Column(String(255), default="unknown")
    rating = Column(String(10), nullable=False)       # Good / Okay / Bad
    score = Column(Float, nullable=False)              # 1-10 numeric score
    cyclomatic_complexity = Column(Integer)
    num_params = Column(Integer)
    num_lines = Column(Integer)
    has_docstring = Column(Integer)
    comment_ratio = Column(Float)
    nesting_depth = Column(Integer)
    num_returns = Column(Integer)
    suggestions = Column(Text)                         # AI-generated suggestions
    improved_code = Column(Text)                       # AI-improved version
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
