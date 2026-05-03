"""
predictor.py — Load trained Random Forest model and predict code quality
"""

import numpy as np
import joblib
from app.config import MODEL_PATH, ENCODER_PATH

# ── Load model at module import time ──
_model = joblib.load(MODEL_PATH)
_encoder = joblib.load(ENCODER_PATH)

FEATURE_ORDER = [
    "cyclomatic_complexity",
    "num_params",
    "num_lines",
    "has_docstring",
    "comment_ratio",
    "nesting_depth",
    "num_returns",
]


def predict(metrics: dict) -> tuple[str, float, float]:
    """
    Predict code quality from metrics.

    Returns:
        (label, confidence, score)
        - label: "Good", "Okay", or "Bad"
        - confidence: 0.0-1.0 probability of predicted class
        - score: 1-10 numeric quality score
    """
    # Build feature vector in correct order
    features = np.array([[metrics[f] for f in FEATURE_ORDER]])

    # Predict
    pred_idx = _model.predict(features)[0]
    probabilities = _model.predict_proba(features)[0]
    confidence = float(probabilities[pred_idx])
    label = str(_encoder.inverse_transform([pred_idx])[0])

    # Calculate numeric score (1-10)
    # Use weighted probabilities: Good contributes high, Bad contributes low
    class_scores = {}
    for i, cls in enumerate(_encoder.classes_):
        if cls == "Good":
            class_scores[i] = 9.0
        elif cls == "Okay":
            class_scores[i] = 6.0
        else:  # Bad
            class_scores[i] = 2.5

    # Weighted score based on probabilities
    score = sum(float(probabilities[i]) * class_scores[i] for i in range(len(probabilities)))

    # Clamp to 1-10
    score = round(max(1.0, min(10.0, score)), 1)

    return label, confidence, float(score)
