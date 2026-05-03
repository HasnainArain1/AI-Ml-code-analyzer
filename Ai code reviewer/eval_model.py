"""Evaluate the trained model on the dataset to get accuracy, precision, recall."""
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

DATASET = "dataset/code_quality.csv"
MODEL   = "artifacts/rf_model.pkl"
ENCODER = "artifacts/label_encoder.pkl"

FEATURES = [
    "cyclomatic_complexity", "num_params", "num_lines",
    "has_docstring", "comment_ratio", "nesting_depth", "num_returns",
]

df = pd.read_csv(DATASET)
model = joblib.load(MODEL)
encoder = joblib.load(ENCODER)

X = df[FEATURES].values
y = encoder.transform(df["label"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

y_pred = model.predict(X_test)

print("=" * 60)
print("  AI Code Reviewer — Model Evaluation Report")
print("=" * 60)
print(f"\n  Dataset size : {len(df)} rows")
print(f"  Train set    : {len(X_train)} rows")
print(f"  Test set     : {len(X_test)} rows")
print(f"  Classes      : {list(encoder.classes_)}")
print(f"\n  Overall Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"\n{'=' * 60}")
print("  Classification Report (per-class precision, recall, F1)")
print("=" * 60)
print(classification_report(y_test, y_pred, target_names=encoder.classes_))
print("  Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("=" * 60)
