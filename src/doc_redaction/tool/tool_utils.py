import json
import shutil
from pathlib import Path

from loguru import logger
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


@tool
def save_file(data: str, filename: str) -> None:
    """Write a formatted string to a file and log the operation.

    Parameters:
        data: String content to write.
        filename: Destination file path. Existing content will be overwritten.

    Returns:
        None

    Raises:
        OSError: If the file cannot be opened or written.

    Logs:
        INFO: On successful save with the target file path.

    Example:
        save_file(res, "data/confidential/rocketbase_aws_agreement_sensitive_structures.json")
    """
    output_dir = Path(filename).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(filename, "w") as f:
        f.write(data)
    logger.info(f"Saved structured output to {filename}")


@tool
def remove_temp_files(path: str = "data/temp/") -> None:
    """
    Remove temporary files in the specified directory.

    Parameters:
        path: Directory path to remove.

    Returns:
        None
    """

    shutil.rmtree(path)
    logger.info(f"Removed temporary files in directory: {path}")
