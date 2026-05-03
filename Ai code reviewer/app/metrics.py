"""
metrics.py — Extract 7 code quality metrics using AST + Radon
Reuses logic from scripts/build_dataset.py
"""

import ast
import textwrap
import radon.complexity as radon_cc


def get_nesting_depth(node, current=0):
    """Recursively find the deepest nesting level."""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.If, ast.With, ast.Try)):
            depth = get_nesting_depth(child, current + 1)
            max_depth = max(max_depth, depth)
    return max_depth


def extract_func_name(code: str) -> str:
    """Extract the function name from code string."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except SyntaxError:
        pass
    return "unknown"


def extract_metrics(code: str) -> dict | None:
    """
    Extract 7 code quality metrics from a Python function string.

    Returns dict with metrics or None if parsing fails.
    """
    # Dedent in case code is indented (e.g., method inside a class)
    code = textwrap.dedent(code)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    # Find first function node
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_node = node
            break

    if func_node is None:
        return None

    try:
        # 1. Cyclomatic complexity (Radon)
        cc_blocks = radon_cc.cc_visit(code)
        complexity = cc_blocks[0].complexity if cc_blocks else 1

        # 2. Number of parameters
        num_params = len(func_node.args.args)

        # 3. Number of lines
        num_lines = (func_node.end_lineno or 1) - func_node.lineno + 1

        # 4. Has docstring
        has_docstring = int(ast.get_docstring(func_node) is not None)

        # 5. Comment ratio
        code_lines = code.splitlines()
        comment_count = sum(1 for line in code_lines if line.strip().startswith("#"))
        comment_ratio = round(comment_count / num_lines, 3) if num_lines > 0 else 0

        # 6. Nesting depth
        nesting_depth = get_nesting_depth(func_node)

        # 7. Return statement count
        num_returns = sum(
            1 for n in ast.walk(func_node) if isinstance(n, ast.Return)
        )

        return {
            "cyclomatic_complexity": complexity,
            "num_params": num_params,
            "num_lines": num_lines,
            "has_docstring": has_docstring,
            "comment_ratio": comment_ratio,
            "nesting_depth": nesting_depth,
            "num_returns": num_returns,
        }

    except Exception:
        return None
