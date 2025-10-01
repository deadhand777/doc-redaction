"""
Tool for redacting sensitive information from markdown documents.
"""

import re
from typing import Any

# from strands import tool
from strands.types.tools import ToolResult, ToolUse

TOOL_SPEC: dict = {
    "name": "redact_sensitive_data",
    "description": "Redact sensitive information from markdown documents based on user-specified criteria. "
    "Supports redacting emails, phone numbers, SSNs, credit cards, names, addresses, "
    "custom patterns, and user-defined sensitive terms.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "markdown_content": {
                    "type": "string",
                    "description": "The markdown document content to redact sensitive information from",
                },
                "redaction_rules": {
                    "type": "string",
                    "description": "User prompt describing what information should be redacted (e.g., 'redact all email addresses and phone numbers', 'remove personal names and SSNs', 'redact credit card numbers')",
                },
                "redaction_symbol": {
                    "type": "string",
                    "description": "Symbol to use for redaction (default: '[REDACTED]')",
                    "default": "[REDACTED]",
                },
                "preserve_structure": {
                    "type": "boolean",
                    "description": "Whether to preserve the original text structure by replacing each character with the redaction symbol (default: False)",
                    "default": False,
                },
            },
            "required": ["markdown_content", "redaction_rules"],
        }
    },
}


def redact_sensitive_data(tool: ToolUse, **kwargs: Any) -> ToolResult:
    """
    Redact sensitive information from markdown documents based on user specifications.

    Args:
        tool: The tool use object containing tool execution details
        **kwargs: Additional arguments passed to the tool

    Returns:
        ToolResult: The redacted markdown document
    """
    try:
        # Extract parameters
        markdown_content = tool.get("input", {}).get("markdown_content", "")
        redaction_rules = tool.get("input", {}).get("redaction_rules", "")
        redaction_symbol = tool.get("input", {}).get("redaction_symbol", "[REDACTED]")
        preserve_structure = tool.get("input", {}).get("preserve_structure", False)

        if not markdown_content:
            return {
                "toolUseId": tool["toolUseId"],
                "status": "error",
                "content": [{"text": "Error: No markdown content provided"}],
            }

        if not redaction_rules:
            return {
                "toolUseId": tool["toolUseId"],
                "status": "error",
                "content": [{"text": "Error: No redaction rules specified"}],
            }

        # Parse redaction rules and apply redactions
        redacted_content = apply_redactions(markdown_content, redaction_rules, redaction_symbol, preserve_structure)

        return {
            "toolUseId": tool["toolUseId"],
            "status": "success",
            "content": [{"text": f"Successfully redacted sensitive information based on rules: '{redaction_rules}'\n\nRedacted markdown document:\n\n{redacted_content}"}],
        }

    except Exception as e:
        return {
            "toolUseId": tool["toolUseId"],
            "status": "error",
            "content": [{"text": f"Error processing redaction: {e!s}"}],
        }


def apply_redactions(content: str, rules: str, redaction_symbol: str, preserve_structure: bool) -> str:
    """
    Apply redaction rules to the content based on user specifications.
    """
    rules_lower = rules.lower()

    # Common patterns
    patterns = {
        "email": (
            [r"email", r"e-mail", "@"],
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ),
        "phone": (
            [r"phone", r"telephone", r"number"],
            r"(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})",
        ),
        "ssn": (
            [r"ssn", r"social security", r"social"],
            r"\b\d{3}-?\d{2}-?\d{4}\b",
        ),
        "credit_card": (
            [r"credit card", r"card number", r"credit"],
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        ),
        "zip_code": (
            [r"zip code", r"postal code", r"zip"],
            r"\b\d{5}(?:-\d{4})?\b",
        ),
        "ip_address": (
            [r"ip address", r"ip"],
            r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        ),
        "url": (
            [r"url", r"link", r"website"],
            r'https?://[^\s<>"{}|\\^`\[\]]+',
        ),
        "date": (
            [r"date", r"birthday", r"birth"],
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        ),
        "name": (
            [r"name", r"person", r"individual"],
            r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
        ),
        "address": (
            [r"address", r"street", r"location"],
            r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)",
        ),
    }

    def should_apply(keywords: list[str]) -> bool:
        return any(term in rules_lower for term in keywords)

    redacted_content = content
    for _, (keywords, pattern) in patterns.items():
        if should_apply(keywords):
            redacted_content = redact_pattern(redacted_content, pattern, redaction_symbol, preserve_structure)

    # Handle custom terms
    for term in extract_custom_terms(rules):
        if term and len(term) > 2:
            pattern = re.escape(term)
            redacted_content = redact_pattern(redacted_content, pattern, redaction_symbol, preserve_structure, case_insensitive=True)

    return redacted_content


def redact_pattern(content: str, pattern: str, redaction_symbol: str, preserve_structure: bool, case_insensitive: bool = False) -> str:
    """
    Redact matches of a specific pattern in the content.
    """
    flags = re.IGNORECASE if case_insensitive else 0

    def replace_match(match):
        matched_text = match.group(0)
        if preserve_structure:
            # Replace each character with a redaction character, preserving spaces and structure
            redaction_char = "█"
            return re.sub(r"\S", redaction_char, matched_text)
        else:
            return redaction_symbol

    return re.sub(pattern, replace_match, content, flags=flags)


def extract_custom_terms(rules: str) -> list[str]:
    """
    Extract potential custom terms to redact from the rules text.
    This is a simple approach - could be enhanced with NLP.
    """
    # Look for quoted terms or terms after "redact"
    custom_terms = []

    # Extract quoted terms
    quoted_terms = re.findall(r"['\"]([^'\"]+)['\"]", rules)
    custom_terms.extend(quoted_terms)

    # Extract terms after "redact" or "remove"
    redact_terms = re.findall(r"(?:redact|remove|hide)\s+(?:all\s+)?([a-zA-Z\s]+?)(?:\s+(?:and|or|from)|$)", rules, re.IGNORECASE)
    for term in redact_terms:
        term = term.strip()
        if term and not any(common in term.lower() for common in ["email", "phone", "number", "address", "name", "ssn", "credit", "card"]):
            custom_terms.append(term)

    return custom_terms
