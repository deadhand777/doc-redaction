import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from loguru import logger


def _basic_file_info(doc: fitz.Document, file_path: str) -> dict[str, Any]:
    return {
        "total_pages": len(doc),
        "file_size_mb": Path(file_path).stat().st_size / (1024 * 1024),
        "is_encrypted": doc.needs_pass,
        "metadata": doc.metadata,
        "is_pdf": doc.is_pdf,
        "page_count": doc.page_count,
    }


def _fonts_used(text_dict: dict[str, Any]) -> set[str]:
    fonts: set[str] = set()
    for block in text_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font = span.get("font")
                if font:
                    fonts.add(font)
    return fonts


def _analyze_page(page: fitz.Page, index: int) -> tuple[dict[str, Any], str, int, int]:
    page_text = page.get_text()
    blocks = page.get_text("blocks")
    images = page.get_images()
    rect = page.rect
    text_area = len(page_text.replace(" ", "").replace("\n", ""))
    page_area = rect.width * rect.height or 1
    density = text_area / page_area
    text_dict = page.get_text("dict")

    page_info: dict[str, Any] = {
        "page_number": index + 1,
        "text_length": len(page_text),
        "text_blocks_count": len(blocks),
        "image_count": len(images),
        "character_count": text_area,
        "word_count": len(page_text.split()),
        "line_count": len(page_text.split("\n")),
        "page_dimensions": {"width": rect.width, "height": rect.height},
        "text_density": density,
        "rotation": page.rotation,
        "has_images": bool(images),
        "is_image_page": bool(images) and len(page_text.strip()) < 50,
        "fonts_used": list(_fonts_used(text_dict)),
    }

    if len(page_text.strip()) < 10:
        page_info["potential_issue"] = "Very little text extracted - possible image-only page"
    elif density < 0.001:
        page_info["potential_issue"] = "Low text density - possible scanned document"
    elif len(images) > 5:
        page_info["note"] = "High image count - complex layout"

    return page_info, page_text, len(blocks), len(images)


def _aggregate_metrics(
    text: str,
    blocks: int,
    images: int,
    page_details: list[dict[str, Any]],
    page_count: int,
) -> dict[str, Any]:
    return {
        "total_characters": len(text),
        "total_words": len(text.split()),
        "total_lines": len(text.split("\n")),
        "total_text_blocks": blocks,
        "total_images": images,
        "average_chars_per_page": (len(text) / page_count) if page_count else 0,
        "pages_with_content": sum(p["text_length"] > 10 for p in page_details),
        "pages_without_content": sum(p["text_length"] <= 10 for p in page_details),
        "image_only_pages": sum(p.get("is_image_page", False) for p in page_details),
        "average_text_density": (sum(p["text_density"] for p in page_details) / len(page_details) if page_details else 0),
    }


def _content_analysis(text: str, pages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "has_meaningful_content": len(text.strip()) > 100,
        "contains_numbers": any(ch.isdigit() for ch in text),
        "contains_special_chars": any(ch in "€$%@#&*" for ch in text),
        "page_details": pages,
    }


def _detect_issues(info: dict[str, Any], metrics: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if info["is_encrypted"]:
        issues.append("Document is encrypted - may affect extraction")
    if metrics["pages_without_content"]:
        issues.append(f"{metrics['pages_without_content']} pages have little/no extractable text")
    if metrics["total_characters"] < 100:
        issues.append("Very little text extracted overall - may contain mostly images")
    if metrics["image_only_pages"]:
        issues.append(f"{metrics['image_only_pages']} pages appear image-only")
    if metrics["average_text_density"] < 0.001:
        issues.append("Low text density - possibly scanned document")
    if metrics["total_images"] > info["total_pages"] * 3:
        issues.append("High image count - complex / graphics-heavy document")
    return issues


def _recommendations(issues: Iterable[str], metrics: dict[str, Any]) -> list[str]:
    issues_joined = " ".join(issues).lower()
    rec: set[str] = set()
    if not issues_joined:
        return ["Text extraction appears successful"]
    if "scanned" in issues_joined or "image-only" in issues_joined:
        rec.add("Consider OCR or visual extraction methods")
    if "high image count" in issues_joined or "graphics" in issues_joined:
        rec.add("Extract images separately for analysis")
    if "encrypted" in issues_joined:
        rec.add("Provide password or decrypt before processing")
    if metrics["average_text_density"] < 0.001:
        rec.add("Fallback to OCR for low density pages")
    return sorted(rec)


def _quality_label(issue_count: int) -> str:
    if issue_count == 0:
        return "high"
    if issue_count <= 2:
        return "medium"
    return "low"


def _save_report(assessment: dict[str, Any], output_path: str) -> None:
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(assessment, indent=2), encoding="utf-8")
    logger.info("Assessment saved to %s", output_path)


def assess_doc_quality(
    file_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Assess document extraction quality (text density, images, structure) for an PDF.

    Args:
        file_path: Local path to the PDF document.
        output_path: Optional path to write JSON assessment.

    Returns:
        Assessment dictionary (file_info, extraction_metrics, content_analysis, potential_issues, recommendations, document_quality).
    """
    document: fitz.Document | None = None
    try:
        document: fitz.Document = fitz.open(file_path)

        file_info = _basic_file_info(document, file_path)

        page_details: list[dict[str, Any]] = []
        total_text = ""
        total_blocks = 0
        total_images = 0

        for idx, page in enumerate(document.pages()):
            page_info, page_text, block_count, image_count = _analyze_page(page, idx)
            page_details.append(page_info)
            total_text += page_text
            total_blocks += block_count
            total_images += image_count

        metrics = _aggregate_metrics(
            total_text,
            total_blocks,
            total_images,
            page_details,
            len(document),
        )
        content = _content_analysis(total_text, page_details)
        issues = _detect_issues(file_info, metrics)
        recs = _recommendations(issues, metrics)
        quality = _quality_label(len(issues))

        assessment: dict[str, Any] = {
            "file_info": file_info,
            "extraction_metrics": metrics,
            "content_analysis": content,
            "potential_issues": issues,
            "recommendations": recs,
            "document_quality": quality,
        }

        if output_path:
            _save_report(assessment, output_path)

        return assessment

    except FileNotFoundError as err:
        logger.error("File access error for %s: %s", file_path, err)
        raise
    except fitz.FileDataError as err:
        logger.error("Corrupted or invalid PDF (%s): %s", file_path, err)
        raise
