"""
Tool for detecting sensitive data in markdown documents.
"""

import re

from strands import tool

# --- Precompiled regex patterns ---

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEXES = [
    re.compile(r"\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"),
    re.compile(r"\(\d{3}\)\s?\d{3}[-.]?\d{4}"),
    re.compile(r"\d{3}[-.]?\d{3}[-.]?\d{4}"),
    re.compile(r"\+\d{1,3}\s\d{1,4}\s\d{4,10}"),
]
CC_RE = re.compile(r"\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}[A-Z0-9]{0,16}\b")
ACCOUNT_RE = re.compile(
    r"\b(?:Account|Acc|A/C)[:\s#]*(\d{8,17}|\d{4}[-\s]\d{4}[-\s]\d{4,9})\b",
    re.IGNORECASE,
)
ADDRESS_REGEXES = [
    re.compile(
        r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Circle|Cir|Court|Ct)\.?\s*,?\s*[A-Za-z\s]*\d{5}(?:-\d{4})?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Circle|Cir|Court|Ct)\.?",
        re.IGNORECASE,
    ),
]
NAME_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b")
CURRENCY_REGEXES = [
    re.compile(r"[€$]\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", re.IGNORECASE),
    re.compile(r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s*(?:EUR|USD|€|\$)", re.IGNORECASE),
    re.compile(r"(?:EUR|USD)\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", re.IGNORECASE),
    re.compile(
        r"\b(?:hundert|tausend|million|milliarde)\s+(?:EUR|USD|€|\$)\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b",
        re.IGNORECASE,
    ),
]
PERCENTAGE_REGEXES = [
    re.compile(r"\d+(?:\.\d+)?%"),
    re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:percent|prozent|percentage)\b", re.IGNORECASE),
]
NUMBER_REGEXES = [
    re.compile(r"\b\d+(?:[.,]\d+)*(?:[.,]\d+)?\b"),  # digits
    re.compile(r"\b(hundert|tausend|million|milliarde)\b", re.IGNORECASE),  # big German numbers
]

# --- German written numbers ---
GERMAN_NUMBER_WORDS = {
    "null",
    "eins",
    "eine",
    "einer",
    "einem",
    "einen",
    "eines",
    "zwei",
    "drei",
    "vier",
    "fünf",
    "sechs",
    "sieben",
    "acht",
    "neun",
    "zehn",
    "elf",
    "zwölf",
    "dreizehn",
    "vierzehn",
    "fünfzehn",
    "sechzehn",
    "siebzehn",
    "achtzehn",
    "neunzehn",
    "zwanzig",
    "dreißig",
    "vierzig",
    "fünfzig",
    "sechzig",
    "siebzig",
    "achtzig",
    "neunzig",
    "hundert",
    "tausend",
    "zehntausend",
    "million",
    "milliarde",
}

# --- English written numbers ---
ENGLISH_NUMBER_WORDS = {
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
    "hundred",
    "thousand",
    "million",
    "billion",
}

# Common false positives for name detection
COMMON_NON_NAMES = {
    "United States",
    "New York",
    "Los Angeles",
    "San Francisco",
    "North America",
    "South America",
    "East Coast",
    "West Coast",
    "Middle East",
    "South Korea",
    "North Korea",
    "Saudi Arabia",
    "United Kingdom",
    "South Africa",
    "New Zealand",
    "Costa Rica",
    "Puerto Rico",
    "Hong Kong",
    "Las Vegas",
    "San Diego",
    "Chief Executive",
    "Vice President",
    "General Manager",
    "Project Manager",
    "Data Science",
    "Machine Learning",
    "Artificial Intelligence",
    "Computer Science",
}


@tool
def detect_sensitive_data(markdown_content: str) -> dict[str, list[str]]:
    """Detects and extracts sensitive information from markdown documents."""

    text = remove_markdown_formatting(markdown_content)
    results: dict[str, list[str]] = {}

    # Mapping of result key -> regex list or single regex
    pattern_mapping = {
        "email_addresses": [EMAIL_RE],
        "phone_numbers": PHONE_REGEXES,
        "credit_card_numbers": [CC_RE],
        "iban_numbers": [IBAN_RE],
        "account_numbers": [ACCOUNT_RE],
        "addresses": ADDRESS_REGEXES,
        "people_names": [NAME_RE],
        "currency_amounts": CURRENCY_REGEXES,
        "percentages": PERCENTAGE_REGEXES,
        "numbers": NUMBER_REGEXES,
    }

    for key, regexes in pattern_mapping.items():
        matches = set()
        for regex in regexes:
            for match in regex.findall(text):
                # Additional filters for some types
                if key == "phone_numbers" and len(re.sub(r"[^\d]", "", match)) < 7:
                    continue
                if key == "credit_card_numbers":
                    digits = re.sub(r"[^\d]", "", match)
                    if not (13 <= len(digits) <= 19):
                        continue
                if key == "people_names" and match in COMMON_NON_NAMES:
                    continue
                matches.add(match)
        if matches:
            results[key] = list(matches)

    # Add German & English number words
    numbers_set = set(results.get("numbers", []))
    for word in text.lower().split():
        clean_word = word.strip(".,;:!?")
        if clean_word in GERMAN_NUMBER_WORDS or clean_word in ENGLISH_NUMBER_WORDS:
            numbers_set.add(clean_word)
    if numbers_set:
        results["numbers"] = list(numbers_set)

    return results


def remove_markdown_formatting(markdown_text: str) -> str:
    """Remove markdown formatting for cleaner analysis."""
    patterns = [
        (r"^#{1,6}\s+", ""),  # headers
        (r"\*\*(.+?)\*\*", r"\1"),  # bold
        (r"\*(.+?)\*", r"\1"),  # italic
        (r"__(.+?)__", r"\1"),  # underline
        (r"_(.+?)_", r"\1"),
        (r"`(.+?)`", r"\1"),  # inline code
        (r"```.*?```", "", re.DOTALL),  # code blocks
        (r"\[(.+?)\]\(.+?\)", r"\1"),  # links
        (r"!\[.*?\]\(.+?\)", ""),  # images
        (r"^---+$", "", re.MULTILINE),  # hr
        (r"^\s*[-*+]\s+", "", re.MULTILINE),  # unordered lists
        (r"^\s*\d+\.\s+", "", re.MULTILINE),  # ordered lists
        (r"^>\s+", "", re.MULTILINE),  # blockquotes
    ]
    text = markdown_text

    for pat in patterns:
        text = (
            re.sub(pat[0], pat[1], text)  # if len(pat) == 2 else re.sub(pat[0], pat[1], text)  # flags=pat[2]
        )

    text = re.sub(r"\n\s*\n", "\n\n", text)  # normalize spacing
    return re.sub(r"[ \t]+", " ", text).strip()
