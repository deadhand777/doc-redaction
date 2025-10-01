from loguru import logger
from strands.tools import tool


@tool
def save_as_json(data: str, filename: str) -> None:
    """Write a JSON-formatted string to a file and log the operation.

    Parameters:
        data: JSON string content to write.
        filename: Destination file path. Existing content will be overwritten.

    Returns:
        None

    Raises:
        OSError: If the file cannot be opened or written.

    Logs:
        INFO: On successful save with the target file path.

    Example:
        save_as_json(res, "data/confidential/rocketbase_aws_agreement_sensitive_structures_v4.json")
    """
    with open(filename, "w") as f:
        f.write(data)
    logger.info(f"Saved structured output to {filename}")
