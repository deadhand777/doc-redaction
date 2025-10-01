from loguru import logger


class MissingArgumentError(ValueError):
    """Raised when a required argument is missing."""

    def __init__(self, argument_name: str) -> None:
        super().__init__(f"{argument_name} must be provided")


class InvalidDocumentKeyError(ValueError):
    """Raised when the provided document key is missing or invalid."""

    def __init__(self) -> None:
        super().__init__("A document key must be provided as a non-empty string.")


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
        save_as_json(res, "data/confidential/rocketbase_aws_agreement_sensitive_structures.json")
    """
    with open(filename, "w") as f:
        f.write(data)
    logger.info(f"Saved structured output to {filename}")
