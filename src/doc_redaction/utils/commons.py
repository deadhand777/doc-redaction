import os

import pypdf
from loguru import logger


class MissingArgumentError(ValueError):
    """Raised when a required argument is missing."""

    def __init__(self, argument_name: str) -> None:
        super().__init__(f"{argument_name} must be provided")


class InvalidContentType(TypeError):
    def __init__(self, actual_type: type):
        # Construct the message once here
        super().__init__(f"Content must be str or int, got {actual_type.__name__}")


class InvalidDocumentKeyError(ValueError):
    """Raised when the provided document key is missing or invalid."""

    def __init__(self) -> None:
        super().__init__("A document key must be provided as a non-empty string.")


class PDFProcessingError(Exception):
    """Raised when PDF processing fails."""

    def __init__(self, file_path: str, e: Exception) -> None:
        super().__init__(f"Could not determine page count for {file_path}: {e}")
        self.file_path = file_path


class ParameterTypeError(TypeError):
    def __init__(self, name: str, expected: str):
        super().__init__(f"Parameter {name!r} must be {expected}")


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


def get_pdf_page_count(file_path: str) -> int:
    """
    Return the number of pages in a PDF file.

    Parameters:
        file_path (str): Path to the local PDF file.

    Returns:
        int: Total number of pages in the PDF.

    Raises:
        PDFProcessingError: If the file cannot be opened, is not a valid PDF, or the page count cannot be determined.

    Example:
        page_count = get_pdf_page_count("path/to/file.pdf")
        print(f"The document has {page_count} pages.")
    """
    try:
        with open(file_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            return len(pdf_reader.pages)
    except Exception as e:
        raise PDFProcessingError(file_path, e) from e


def get_file_size(file_path: str) -> int:
    """
    Return the size of a file in bytes.

        Parameters:
            file_path (str): Path to the file.

        Returns:
            int: File size in bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
            OSError: If the size cannot be retrieved due to an OS-related error.

        Example:
            size = get_file_size("/path/to/file.txt")
            print(f"File size: {size} bytes")
    """
    return os.path.getsize(file_path)
