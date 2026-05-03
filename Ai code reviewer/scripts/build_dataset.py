"""
build_dataset.py
----------------
Collects Python functions from local Python installation
(stdlib + installed packages like requests, flask, pandas).

Pipeline:
  1. Collect .py files
  2. Extract individual functions using AST
  3. Extract 7 code quality metrics (AST + Radon)
  4. Auto-label: Good / Okay / Bad
  5. Balance labels and save to CSV

Output: dataset/code_quality.csv
"""

import ast
import csv
import os
import sys
import random
import textwrap
import pandas as pd
import radon.complexity as radon_cc


# ─────────────────────────────────────────────
# CONFIG — auto detects Windows & Linux paths
# ─────────────────────────────────────────────

def get_sources():
    sources = set()

    # Python stdlib (e.g. E:\Lib)
    stdlib = os.path.dirname(os.__file__)
    sources.add(stdlib)

    # venv site-packages (e.g. D:\project\.venv\Lib\site-packages)
    for path in [
        os.path.join(sys.prefix, "Lib", "site-packages"),      # Windows venv
        os.path.join(sys.prefix, "lib", "site-packages"),      # Linux venv
        os.path.join(sys.base_prefix, "Lib", "site-packages"), # Windows system
        os.path.join(sys.base_prefix, "lib", "site-packages"), # Linux system
    ]:
        if os.path.exists(path):
            sources.add(path)

    # Also try site module
    try:
        import site
        for path in site.getsitepackages():
            if os.path.exists(path):
                sources.add(path)
    except Exception:
        pass

    sources = [s for s in sources if os.path.exists(s)]
    print(f"      Detected source paths:")
    for s in sources:
        print(f"        {s}")
    return sources

SOURCES          = []           # filled at runtime by get_sources()
TARGET_PER_LABEL = 400
MAX_FILES        = 600
OUTPUT_PATH      = "dataset/code_quality.csv"
RANDOM_SEED      = 42

TARGET_PER_LABEL = 400    # 400 Good + 400 Okay + 400 Bad = 1200 total
MAX_FILES        = 600    # scan up to this many .py files
OUTPUT_PATH      = "dataset/code_quality.csv"
RANDOM_SEED      = 42

random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────
# STEP 1 — COLLECT .py FILES
# ─────────────────────────────────────────────

def collect_py_files():
    all_files = []
    sources = get_sources()
    for source in sources:
        if not os.path.exists(source):
            continue
        for root, dirs, files in os.walk(source):
            # Skip test dirs and cache
            dirs[:] = [
                d for d in dirs
                if not d.startswith(("test", ".", "__pycache__"))
            ]
            for f in files:
                if f.endswith(".py") and not f.startswith("test_"):
                    all_files.append(os.path.join(root, f))

    random.shuffle(all_files)
    selected = all_files[:MAX_FILES]

    print(f"      Total .py files found : {len(all_files)}")
    print(f"      Files selected to scan: {len(selected)}")
    return selected


# ─────────────────────────────────────────────
# STEP 2 — EXTRACT FUNCTIONS
# ─────────────────────────────────────────────

def extract_functions_from_file(filepath):
    """Return list of {func_name, code, file} from a .py file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines     = source.splitlines()
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            try:
                start       = node.lineno - 1
                end         = node.end_lineno
                func_source = "\n".join(lines[start:end])

                # KEY FIX: dedent so radon can parse nested functions
                func_source = textwrap.dedent(func_source)

                functions.append({
                    "func_name": node.name,
                    "code":      func_source,
                    "file":      os.path.basename(filepath),
                })
            except Exception:
                continue

    return functions


# ─────────────────────────────────────────────
# STEP 3 — VALIDATE
# ─────────────────────────────────────────────

def is_valid(code):
    """Filter out too-short, too-long, or unparseable functions."""
    if not isinstance(code, str):  return False
    if len(code.strip()) < 30:     return False  # trivially small
    if code.count("\n") < 2:       return False  # one-liner
    if "def " not in code:         return False  # safety check
    if len(code) > 3000:           return False  # too large
    return True


# ─────────────────────────────────────────────
# STEP 4 — EXTRACT METRICS
# ─────────────────────────────────────────────

def get_nesting_depth(node, current=0):
    """Recursively find the deepest nesting level."""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.If, ast.With, ast.Try)):
            depth     = get_nesting_depth(child, current + 1)
            max_depth = max(max_depth, depth)
    return max_depth


def extract_metrics(code):
    """
    Extract 7 code quality metrics from a function string.

    Metrics:
      cyclomatic_complexity — number of linearly independent paths (Radon)
      num_params            — number of parameters
      num_lines             — total lines in function
      has_docstring         — 1 if docstring present, else 0
      comment_ratio         — comment lines / total lines
      nesting_depth         — deepest level of nested if/for/while/try
      num_returns           — count of return statements

    Returns dict or None if parsing fails.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    # Get top-level function node
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_node = node
            break

    if func_node is None:
        return None

    try:
        # 1. Cyclomatic complexity via Radon (needs dedented code)
        cc_blocks  = radon_cc.cc_visit(code)
        complexity = cc_blocks[0].complexity if cc_blocks else 1

        # 2. Parameters (excluding self/cls)
        params     = func_node.args.args
        num_params = len(params)

        # 3. Lines
        num_lines  = (func_node.end_lineno or 1) - func_node.lineno + 1

        # 4. Docstring
        has_docstring = int(ast.get_docstring(func_node) is not None)

        # 5. Comment ratio
        code_lines    = code.splitlines()
        comment_count = sum(1 for l in code_lines if l.strip().startswith("#"))
        comment_ratio = round(comment_count / num_lines, 3) if num_lines > 0 else 0

        # 6. Nesting depth
        nesting_depth = get_nesting_depth(func_node)

        # 7. Return statements
        num_returns = sum(
            1 for n in ast.walk(func_node) if isinstance(n, ast.Return)
        )

        return {
            "cyclomatic_complexity": complexity,
            "num_params":            num_params,
            "num_lines":             num_lines,
            "has_docstring":         has_docstring,
            "comment_ratio":         comment_ratio,
            "nesting_depth":         nesting_depth,
            "num_returns":           num_returns,
        }

    except Exception:
        return None


# ─────────────────────────────────────────────
# STEP 5 — AUTO LABEL
# ─────────────────────────────────────────────

def auto_label(row):
    """
    Rule-based scoring based on:
      - Clean Code (Robert Martin): small functions, few params
      - McCabe: complexity > 10 is high risk
      - PEP 257: docstrings are expected
      - PEP 8: comment your code

    Scoring:
      Start at 10, deduct for each bad metric.
      8–10 = Good | 5–7 = Okay | 1–4 = Bad
    """
    score = 10

    # Cyclomatic complexity (most critical)
    if   row["cyclomatic_complexity"] > 10: score -= 3
    elif row["cyclomatic_complexity"] >  5: score -= 1

    # Too many parameters
    if   row["num_params"] > 5: score -= 2
    elif row["num_params"] > 3: score -= 1

    # Missing docstring
    if row["has_docstring"] == 0: score -= 1

    # Too few comments
    if row["comment_ratio"] < 0.05: score -= 1

    # Deep nesting (hard to read)
    if   row["nesting_depth"] > 3: score -= 2
    elif row["nesting_depth"] > 2: score -= 1

    # Too long (violates single responsibility)
    if row["num_lines"] > 50: score -= 1

    score = max(1, score)

    if   score >= 8: return "Good"
    elif score >= 5: return "Okay"
    else:            return "Bad"


# ─────────────────────────────────────────────
# STEP 6 — BALANCE LABELS
# ─────────────────────────────────────────────

def balance_labels(df, target_per_label=TARGET_PER_LABEL):
    """
    Undersample majority classes so all 3 labels have equal rows.
    This prevents ML model from being biased toward 'Good'.
    """
    groups = []
    for label in ["Good", "Okay", "Bad"]:
        group = df[df["label"] == label]
        if len(group) >= target_per_label:
            group = group.sample(target_per_label, random_state=RANDOM_SEED)
        else:
            # If not enough, take all available
            print(f"      Warning: only {len(group)} '{label}' samples available")
        groups.append(group)

    balanced = pd.concat(groups).sample(frac=1, random_state=RANDOM_SEED)
    return balanced.reset_index(drop=True)


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def build_dataset():
    print("\n" + "=" * 55)
    print("   AI Code Reviewer — Dataset Builder")
    print("=" * 55)

    # Step 1 — Collect files
    print("\n[1/5] Collecting .py files from local Python install...")
    py_files = collect_py_files()

    # Step 2 — Extract functions
    print("\n[2/5] Extracting functions using AST...")
    all_functions = []
    for filepath in py_files:
        funcs = extract_functions_from_file(filepath)
        all_functions.extend(funcs)
    print(f"      Raw functions extracted: {len(all_functions)}")

    # Step 3 — Filter
    print("\n[3/5] Filtering invalid functions...")
    valid = [f for f in all_functions if is_valid(f["code"])]
    random.shuffle(valid)
    print(f"      Valid functions: {len(valid)}")

    # Step 4 — Extract metrics
    print("\n[4/5] Extracting metrics (AST + Radon)...")
    rows   = []
    failed = 0

    for item in valid:
        metrics = extract_metrics(item["code"])
        if metrics:
            rows.append({
                "func_name": item["func_name"],
                "file":      item["file"],
                "code":      item["code"],
                **metrics,
            })
        else:
            failed += 1

    print(f"      Extracted: {len(rows)} | Failed: {failed}")

    # Step 5 — Label + Balance + Save
    print("\n[5/5] Labeling, balancing, and saving...")
    df          = pd.DataFrame(rows)
    df["label"] = df.apply(auto_label, axis=1)

    print(f"\n      Before balancing:")
    for label, count in df["label"].value_counts().items():
        print(f"        {label:<6} → {count}")

    df = balance_labels(df)

    print(f"\n      After balancing:")
    for label, count in df["label"].value_counts().items():
        print(f"        {label:<6} → {count}")

    # Print summary
    print(f"\n{'=' * 55}")
    print(f"  FINAL DATASET SUMMARY")
    print(f"{'=' * 55}")
    print(f"  Total rows  : {len(df)}")
    print(f"  Columns     : {list(df.columns)}")
    print(f"\n  Metric averages (across all labels):")
    metric_cols = [
        "cyclomatic_complexity", "num_params", "num_lines",
        "has_docstring", "comment_ratio", "nesting_depth", "num_returns"
    ]
    for col in metric_cols:
        print(f"    {col:<30} avg = {df[col].mean():.2f}")
    print(f"{'=' * 55}\n")

    # Save
    os.makedirs("dataset", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, quoting=csv.QUOTE_ALL)
    print(f"  Saved → {OUTPUT_PATH}")

    return df


if __name__ == "__main__":
    df = build_dataset()

    preview_cols = [
        "func_name", "cyclomatic_complexity", "num_params",
        "num_lines", "has_docstring", "nesting_depth", "label"
    ]
    print("\nSample rows (8 random):")
    print(df[preview_cols].sample(8, random_state=1).to_string(index=False))