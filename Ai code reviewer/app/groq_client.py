"""
groq_client.py — xAI Grok API for AI-powered code suggestions
Uses OpenAI-compatible API with xAI base URL
"""

from openai import OpenAI
from app.config import XAI_API_KEY, XAI_MODEL, XAI_BASE_URL

_client = OpenAI(
    api_key=XAI_API_KEY,
    base_url=XAI_BASE_URL,
)


def get_suggestions(code: str, metrics: dict, rating: str, score: float) -> tuple[str, str]:
    """
    Get AI-powered code improvement suggestions and an improved version.

    Returns:
        (suggestions, improved_code)
    """
    prompt = f"""You are an expert Python code reviewer. Analyze the following Python function and provide:

1. **SUGGESTIONS**: A numbered list of specific, actionable improvements. Cover:
   - Code quality and readability
   - Best practices (PEP 8, PEP 257)
   - Performance optimizations
   - Error handling
   - Documentation

2. **IMPROVED CODE**: A complete, improved version of the function implementing ALL your suggestions.

## Code to Review:
```python
{code}
```

## Metrics:
- Cyclomatic Complexity: {metrics['cyclomatic_complexity']}
- Parameters: {metrics['num_params']}
- Lines: {metrics['num_lines']}
- Has Docstring: {'Yes' if metrics['has_docstring'] else 'No'}
- Comment Ratio: {metrics['comment_ratio']:.1%}
- Nesting Depth: {metrics['nesting_depth']}
- Return Statements: {metrics['num_returns']}

## Current Rating: {rating} (Score: {score}/10)

## Response Format (STRICT):
SUGGESTIONS:
1. ...
2. ...
3. ...

IMPROVED_CODE:
```python
<complete improved function here>
```

Only respond with the suggestions and improved code. No extra commentary."""

    try:
        response = _client.chat.completions.create(
            model=XAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior Python developer and code quality expert. Provide practical, specific code review feedback. Always return both suggestions and improved code.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content or ""
        return _parse_response(content, code)

    except Exception as e:
        fallback_suggestions = _generate_fallback_suggestions(metrics, rating)
        return fallback_suggestions, code


def _parse_response(content: str, original_code: str) -> tuple[str, str]:
    """Parse AI response into suggestions and improved code."""
    suggestions = ""
    improved_code = ""

    # Split by IMPROVED_CODE marker
    if "IMPROVED_CODE:" in content:
        parts = content.split("IMPROVED_CODE:", 1)
        suggestions_part = parts[0]
        code_part = parts[1]
    elif "```python" in content:
        # Try to find code block
        parts = content.split("```python", 1)
        suggestions_part = parts[0]
        code_part = "```python" + parts[1]
    else:
        return content.strip(), original_code

    # Clean suggestions
    if "SUGGESTIONS:" in suggestions_part:
        suggestions = suggestions_part.split("SUGGESTIONS:", 1)[1].strip()
    else:
        suggestions = suggestions_part.strip()

    # Extract code from code block
    if "```python" in code_part:
        code_start = code_part.index("```python") + len("```python")
        code_end = code_part.index("```", code_start) if "```" in code_part[code_start:] else len(code_part)
        improved_code = code_part[code_start:code_start + (code_end - code_start) if "```" in code_part[code_start:] else len(code_part)].strip()
    elif "```" in code_part:
        code_start = code_part.index("```") + 3
        remaining = code_part[code_start:]
        code_end = remaining.index("```") if "```" in remaining else len(remaining)
        improved_code = remaining[:code_end].strip()
    else:
        improved_code = code_part.strip()

    if not improved_code:
        improved_code = original_code

    return suggestions.strip(), improved_code.strip()


def _generate_fallback_suggestions(metrics: dict, rating: str) -> str:
    """Generate rule-based suggestions if AI API fails."""
    suggestions = []

    if not metrics["has_docstring"]:
        suggestions.append("Add a docstring explaining the function's purpose, parameters, and return value (PEP 257).")

    if metrics["cyclomatic_complexity"] > 10:
        suggestions.append(f"Cyclomatic complexity is {metrics['cyclomatic_complexity']} (high). Break this function into smaller, focused helper functions.")
    elif metrics["cyclomatic_complexity"] > 5:
        suggestions.append(f"Cyclomatic complexity is {metrics['cyclomatic_complexity']} (moderate). Consider simplifying conditional logic.")

    if metrics["num_params"] > 5:
        suggestions.append(f"Function has {metrics['num_params']} parameters. Consider using a dataclass or dictionary to group related parameters.")
    elif metrics["num_params"] > 3:
        suggestions.append(f"Function has {metrics['num_params']} parameters. Consider if some can be combined or have defaults.")

    if metrics["nesting_depth"] > 3:
        suggestions.append(f"Nesting depth of {metrics['nesting_depth']} makes code hard to read. Use early returns (guard clauses) to flatten the structure.")

    if metrics["comment_ratio"] < 0.05:
        suggestions.append("Add inline comments explaining complex logic sections.")

    if metrics["num_lines"] > 50:
        suggestions.append(f"Function is {metrics['num_lines']} lines long. Extract logical blocks into separate functions (Single Responsibility Principle).")

    if not suggestions:
        suggestions.append("Code looks good! Minor improvements could include adding type hints and more descriptive variable names.")

    return "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))
