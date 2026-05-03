"""
train_model.py
--------------
Train a Random Forest classifier on code_quality.csv
and save the model + label encoder to artifacts/
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix

# ── Config ──────────────────────────────────────
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "code_quality.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "rf_model.pkl")
ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "label_encoder.pkl")

FEATURE_COLS = [
    "cyclomatic_complexity",
    "num_params",
    "num_lines",
    "has_docstring",
    "comment_ratio",
    "nesting_depth",
    "num_returns",
]

RANDOM_SEED = 42


def train():
    print("\n" + "=" * 55)
    print("   AI Code Reviewer — Model Training")
    print("=" * 55)

    # ── Load dataset ──
    print("\n[1/4] Loading dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"      Loaded {len(df)} rows")
    print(f"      Label distribution:")
    for label, count in df["label"].value_counts().items():
        print(f"        {label:<6} → {count}")

    # ── Prepare features ──
    print("\n[2/4] Preparing features...")
    X = df[FEATURE_COLS].values
    le = LabelEncoder()
    y = le.fit_transform(df["label"])  # Bad=0, Good=1, Okay=2
    print(f"      Features shape: {X.shape}")
    print(f"      Label mapping: {dict(zip(le.classes_, le.transform(le.classes_)))}")

    # ── Train/test split ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    print(f"      Train: {len(X_train)} | Test: {len(X_test)}")

    # ── Train Random Forest ──
    print("\n[3/4] Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ── Evaluate ──
    y_pred = model.predict(X_test)
    accuracy = (y_pred == y_test).mean()
    print(f"\n      Accuracy: {accuracy:.4f}")
    print(f"\n      Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    print(f"      Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))


    # ── Feature importance ──
    print(f"\n      Feature Importance:")
    for name, imp in sorted(
        zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1]
    ):
        bar = "█" * int(imp * 40)
        print(f"        {name:<25} {imp:.4f} {bar}")

    # ── Save ──
    print("\n[4/4] Saving model...")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"      Model  → {MODEL_PATH}")
    print(f"      Encoder → {ENCODER_PATH}")

    #     # ── Overfit Check ──
    # train_accuracy = model.score(X_train, y_train)
    # test_accuracy  = model.score(X_test, y_test)

    # print(f"\n      Train Accuracy : {train_accuracy:.4f}")
    # print(f"      Test Accuracy  : {test_accuracy:.4f}")
    # print(f"      Gap            : {train_accuracy - test_accuracy:.4f}")

    # if train_accuracy - test_accuracy > 0.05:
    #     print("Overfitting!")
    # else:
    #     print("Model generalizes")

    print("=" * 55)




if __name__ == "__main__":
    train()
