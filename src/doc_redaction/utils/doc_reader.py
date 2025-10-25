import mimetypes
import pathlib
from pathlib import Path

import fitz  # via PyMuPDF
from loguru import logger

from doc_redaction.utils.commons import InvalidDocumentFormatError

SUPPORTED_DOCUMENT_FORMATS: set = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".html", ".md", ".txt"}
SUPPORTED_IMAGE_FORMATS: set = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MIME_TYPE_MAP: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


class PDFNotFoundError(FileNotFoundError):
    """Raised when the specified PDF file does not exist."""

    def __init__(self, pdf_path: Path) -> None:
        super().__init__(f"PDF not found: {pdf_path}")
        self.pdf_path = pdf_path


class PDFOpenError(ValueError):
    """Raised when a PDF cannot be opened with PyMuPDF."""

    def __init__(self, pdf_path: str, original_error: Exception) -> None:
        super().__init__(f"Cannot open PDF '{pdf_path}': {original_error}")
        self.pdf_path = pdf_path
        self.original_error = original_error


def get_file_type(object_key: str) -> str:
    """
    Return the file category inferred from an object's extension.

    Parameters:
        object_key (str): Object key or filename.

    Returns:
        str: 'document' for supported document extensions or 'image' for supported image extensions.

    Raises:
        ValueError: If the extension is not supported.

    Examples:
        >>> get_file_type("example.pdf")
        'document'
        >>> get_file_type("image.png")
        'image'
        >>> get_file_type("unsupported_file.xyz")
        Traceback (most recent call last):
            ...
        ValueError: Unsupported file format: .foo. Supported formats are: .xls, .doc, .xlsx, .pdf, .txt, .html, .png, .webp, .gif, .docx, .csv, .jpg, .md, .jpeg.
    """
    file_extension: str = Path(object_key).suffix.lower()
    logger.info(f"file extension: {file_extension}")

    if file_extension in SUPPORTED_DOCUMENT_FORMATS:
        return "document"
    elif file_extension in SUPPORTED_IMAGE_FORMATS:
        return "image"
    else:
        raise InvalidDocumentFormatError(file_extension)


def get_mime_type(object_key: str) -> str:
    """
    Return the MIME type for a given object key or filename.

    Attempts mimetypes.guess_type first; if unavailable, infers from the file
    extension via a fallback map and defaults to 'application/octet-stream'.

    Parameters:
        object_key: Object key or filename, typically including an extension.

    Returns:
        The resolved MIME type string.

    Examples:
        >>> get_mime_type("document.pdf")
        'application/pdf'
        >>> get_mime_type("image.png")
        'image/png'
    """
    mime_type, _ = mimetypes.guess_type(object_key)
    logger.info(f"guessed mime type: {mime_type}")
    if mime_type is None:
        file_extension: str = Path(object_key).suffix.lower()
        mime_type = MIME_TYPE_MAP.get(file_extension, "application/octet-stream")
    return mime_type


def pdf_to_png(
    pdf_path: str | pathlib.Path,
    output_dir: str | pathlib.Path,
    dpi: int = 200,
    prefix: str = "page",
) -> list[str]:
    """
    Convert each page of *pdf_path* into a PNG file in *output_dir*.

    Parameters
    ----------
    pdf_path : str | Path
        Path to the source PDF.
    output_dir : str | Path
        Directory where PNGs will be written.  Will be created if it does not exist.
    dpi : int, optional
        Rendering resolution.  Higher DPI → larger, sharper images.
    prefix : str, optional
        Prefix for the output file names (default "page").

    Returns
    -------
    List[str]
        List of absolute file paths to the created PNGs, in page order.

    Raises
    ------
    FileNotFoundError
        If *pdf_path* does not exist.
    ValueError
        If the PDF cannot be opened.
    """
    pdf_path = pathlib.Path(pdf_path).expanduser().resolve()
    output_dir = pathlib.Path(output_dir).expanduser().resolve()

    if not pdf_path.is_file():
        raise PDFNotFoundError(pdf_path)

    # create the output folder if necessary
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)  # PyMuPDF opens the file
    except Exception as exc:
        raise PDFOpenError(pdf_path, exc) from exc

    png_paths = []

    # iterate pages
    for page_number in range(len(doc)):
        page = doc[page_number]

        # Render page to a pixmap at the requested DPI
        # (transform: zoom factor = dpi / 72)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)  # scaling matrix
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Build the output file name
        out_file = output_dir / f"{prefix}_{str(page_number + 1).zfill(2)}.png"
        pix.save(out_file)
        png_paths.append(str(out_file))

    # cleanup
    doc.close()

    return png_paths


def merge_markdown_strings(pages: list[str], output_file: str) -> str:
    """
    Merge multiple text strings into a single Markdown file,
    treating each string as a page and numbering them.

    Args:
        pages (List[str]): List of text strings, each representing a page.
        output_file (str): Path to the merged output Markdown file.
    """
    merged_content = []

    for page_num, content in enumerate(pages, start=1):
        page_header = f"# Page {page_num}\n\n"
        merged_content.append(page_header + content.strip() + "\n\n---\n")

    final_md: str = "\n".join(merged_content)
    file_name: str = f"{output_file}.md"
    # upload_to_s3(data=final_md, key=file_name, content_type="text/markdown")

    logger.info(f"Merged Markdown saved to: {file_name}")

    return final_md
