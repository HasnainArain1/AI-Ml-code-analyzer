"""
differ.py — Generate unified diff between original and improved code
"""

import difflib


def generate_diff(original: str, improved: str) -> str:
    """
    Generate a unified diff between original and improved code.

    Returns formatted diff string with +/- markers.
    """
    original_lines = original.strip().splitlines(keepends=True)
    improved_lines = improved.strip().splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        improved_lines,
        fromfile="original.py",
        tofile="improved.py",
        lineterm="",
    )

    return "\n".join(diff)
