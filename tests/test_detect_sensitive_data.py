from src.doc_redaction.tool.detect_sensitive_data import (
    ACCOUNT_RE,
    ADDRESS_REGEXES,
    CC_RE,
    CURRENCY_REGEXES,
    EMAIL_RE,
    IBAN_RE,
    NAME_RE,
    NUMBER_REGEXES,
    PERCENTAGE_REGEXES,
    PHONE_REGEXES,
    detect_sensitive_data,
)


class TestDetectSensitiveData:
    """Test suite for the detect_sensitive_data function."""

    def test_detect_email_addresses(self):
        """Test detection of email addresses."""
        markdown_content = "Contact john.doe@example.com or admin@company.org for support."

        result = detect_sensitive_data(markdown_content)

        assert "email_addresses" in result
        assert "john.doe@example.com" in result["email_addresses"]
        assert "admin@company.org" in result["email_addresses"]

    def test_detect_phone_numbers(self):
        """Test detection of various phone number formats."""
        markdown_content = """
        Call us at (555) 123-4567 or +1-800-555-0123
        International: +49 30 12345678
        Simple: 555.123.4567
        """

        result = detect_sensitive_data(markdown_content)

        assert "phone_numbers" in result

        phone_numbers = result["phone_numbers"]

        assert any("555" in phone and "123" in phone and "4567" in phone for phone in phone_numbers)
        assert any("+1" in phone or "800" in phone for phone in phone_numbers)

    def test_detect_credit_card_numbers(self):
        """Test detection of credit card numbers."""
        markdown_content = """
        Card: 1234 5678 9012 3456
        Another: 4111-1111-1111-1111
        """

        result = detect_sensitive_data(markdown_content)

        assert "credit_card_numbers" in result
        cc_numbers = result["credit_card_numbers"]
        assert any("1234 5678 9012 3456" in cc for cc in cc_numbers)
        assert any("4111-1111-1111-1111" in cc for cc in cc_numbers)

    def test_detect_iban_numbers(self):
        """Test detection of IBAN numbers."""
        markdown_content = "Bank account: DE89370400440532013000 or GB29NWBK60161331926819"

        result = detect_sensitive_data(markdown_content)

        assert "iban_numbers" in result
        assert "DE89370400440532013000" in result["iban_numbers"]
        assert "GB29NWBK60161331926819" in result["iban_numbers"]

    def test_detect_account_numbers(self):
        """Test detection of account numbers."""
        markdown_content = "Account: 12345678901 or A/C 1234-5678-9012"

        result = detect_sensitive_data(markdown_content)

        assert "account_numbers" in result
        account_numbers = result["account_numbers"]
        assert any("12345678901" in acc for acc in account_numbers)

    def test_detect_addresses(self):
        """Test detection of street addresses."""
        markdown_content = """
        Visit us at 123 Main Street, Anytown 12345
        Or our office at 456 Oak Avenue
        """

        result = detect_sensitive_data(markdown_content)

        assert "addresses" in result
        addresses = result["addresses"]
        assert any("123 Main Street" in addr for addr in addresses)
        assert any("456 Oak Avenue" in addr for addr in addresses)

    def test_detect_people_names(self):
        """Test detection of people names."""
        markdown_content = "John Smith and Jane Doe at the conference."

        result = detect_sensitive_data(markdown_content)

        assert "people_names" in result
        assert "John Smith" in result["people_names"]
        assert "Jane Doe" in result["people_names"]

    def test_filter_common_non_names(self):
        """Test that common non-names are filtered out."""
        markdown_content = "Visit New York and United States, meet John Smith there."

        result = detect_sensitive_data(markdown_content)

        # Should detect John Smith but not New York or United States
        if "people_names" in result:
            names = result["people_names"]
            assert "John Smith" in names
            assert "New York" not in names
            assert "United States" not in names

    def test_detect_currency_amounts(self):
        """Test detection of currency amounts."""
        markdown_content = """
        Price: €1,234.56 or $999.99
        Cost: 1000 EUR or USD 500.00
        """

        result = detect_sensitive_data(markdown_content)

        assert "currency_amounts" in result
        currencies = result["currency_amounts"]
        assert any("€1,234.56" in curr or "1,234.56" in curr for curr in currencies)
        assert any("$999.99" in curr or "999.99" in curr for curr in currencies)

    def test_detect_percentages(self):
        """Test detection of percentages."""
        markdown_content = "Interest rate: 5.5% or 10 percent discount"

        result = detect_sensitive_data(markdown_content)

        assert "percentages" in result
        percentages = result["percentages"]
        assert "5.5%" in percentages
        assert any("10" in pct and "percent" in pct for pct in percentages)

    def test_detect_numbers(self):
        """Test detection of numbers."""
        markdown_content = "Quantity: 1000 items, price 25.99, ID 123456"

        result = detect_sensitive_data(markdown_content)

        assert "numbers" in result
        numbers = result["numbers"]
        assert "1000" in numbers
        assert "25.99" in numbers
        assert "123456" in numbers

    def test_detect_german_number_words(self):
        """Test detection of German written numbers."""
        markdown_content = "Ich habe hundert Euro und drei Äpfel."

        result = detect_sensitive_data(markdown_content)

        assert "numbers" in result
        numbers = result["numbers"]
        assert "hundert" in numbers
        assert "drei" in numbers

    def test_detect_english_number_words(self):
        """Test detection of English written numbers."""
        markdown_content = "I have twenty dollars and five apples."

        result = detect_sensitive_data(markdown_content)

        assert "numbers" in result
        numbers = result["numbers"]
        assert "twenty" in numbers
        assert "five" in numbers

    def test_phone_number_length_filter(self):
        """Test that phone numbers with insufficient digits are filtered out."""
        markdown_content = "Call 123 or (555) 123-4567"

        result = detect_sensitive_data(markdown_content)

        if "phone_numbers" in result:
            phone_numbers = result["phone_numbers"]
            # Should not include "123" (too short)
            assert not any(phone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "") == "123" for phone in phone_numbers)
            # Should include the valid phone number
            assert any("555" in phone and "123" in phone and "4567" in phone for phone in phone_numbers)

    def test_credit_card_length_filter(self):
        """Test that credit card numbers with invalid lengths are filtered out."""
        markdown_content = "Card: 123456 or 1234-5678-9012-3456"

        result = detect_sensitive_data(markdown_content)

        if "credit_card_numbers" in result:
            cc_numbers = result["credit_card_numbers"]
            # Should not include "123456" (too short)
            assert "123456" not in cc_numbers
            # Should include valid credit card
            assert any("1234-5678-9012-3456" in cc for cc in cc_numbers)

    def test_empty_markdown_content(self):
        """Test with empty markdown content."""
        result = detect_sensitive_data("")

        # Should return empty dict or dict with empty lists
        assert isinstance(result, dict)

    def test_no_sensitive_data(self):
        """Test with content containing no sensitive data."""
        markdown_content = "This is just plain text with no sensitive information."

        result = detect_sensitive_data(markdown_content)

        # Should return empty dict or not include keys for missing data
        assert isinstance(result, dict)

    def test_mixed_sensitive_data(self):
        """Test comprehensive detection with mixed sensitive data types."""
        markdown_content = """
        # Contact Information
        **Name**: Max Mustermann
        **Email**: john.smith@company.com
        **Phone**: (555) 123-4567
        **Address**: 123 Main Street, Anytown 12345
        **Account**: 1234567890123456
        **IBAN**: DE89370400440532013000

        ## Financial Details
        **Amount**: €1,500.00
        **Interest**: 3.5%
        **Quantity**: fifty items
        """

        result = detect_sensitive_data(markdown_content)
        result.keys()

        detected_keys = list(result.keys())
        assert len(detected_keys) > 0

        # Verify specific detections
        if "email_addresses" in result:
            assert "john.smith@company.com" in result["email_addresses"]
        if "numbers" in result:
            assert "fifty" in result["numbers"]

    def test_unicode_content(self):
        """Test detection with Unicode/international content."""
        markdown_content = "Contact José García at josé@example.com or München office."
        result = detect_sensitive_data(markdown_content)

        # Should handle Unicode properly
        if "email_addresses" in result:
            assert "josé@example.com" in result["email_addresses"]

    def test_case_insensitive_patterns(self):
        """Test case-insensitive pattern matching."""
        markdown_content = "ACCOUNT: 123456789 or account: 987654321"

        result = detect_sensitive_data(markdown_content)

        if "account_numbers" in result:
            account_numbers = result["account_numbers"]
            assert any("123456789" in acc for acc in account_numbers)
            assert any("987654321" in acc for acc in account_numbers)

    def test_regex_pattern_compilation(self):
        """Test that all regex patterns compile correctly."""
        patterns = [EMAIL_RE, CC_RE, IBAN_RE, ACCOUNT_RE, NAME_RE]
        pattern_lists = [PHONE_REGEXES, ADDRESS_REGEXES, CURRENCY_REGEXES, PERCENTAGE_REGEXES, NUMBER_REGEXES]

        # Test individual patterns
        for pattern in patterns:
            assert hasattr(pattern, "findall")

        # Test pattern lists
        for pattern_list in pattern_lists:
            for pattern in pattern_list:
                assert hasattr(pattern, "findall")

    def test_deduplication(self):
        """Test that duplicate matches are removed."""
        markdown_content = "Email john@example.com twice: john@example.com"

        result = detect_sensitive_data(markdown_content)

        if "email_addresses" in result:
            # Should only appear once due to set() usage
            assert result["email_addresses"].count("john@example.com") == 1
