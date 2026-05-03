"""
config.py — Application settings loaded from .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:hasnain@localhost:5432/aicodereview")
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_MODEL = "grok-3-mini"  # Fast, excellent for code suggestions
XAI_BASE_URL = "https://api.x.ai/v1"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "rf_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "label_encoder.pkl")
