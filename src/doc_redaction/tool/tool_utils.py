import json

from strands import tool


@tool
def omit_empty_keys(s: str) -> dict[str, list[str]]:
    """
    Parse a JSON object string and return only the items with non-empty values.

    Args:
        s: A JSON-encoded object mapping string keys to lists of strings.

    Returns:
        A dict[str, list[str]] containing only entries whose values are truthy (e.g., non-empty lists).

    Raises:
        json.JSONDecodeError: If the input is not valid JSON.
    """
    return {key: value for key, value in json.loads(s).items() if value}
