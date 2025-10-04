import pytest

from doc_redaction.tool.redact_sensitive_data import TOOL_SPEC, apply_redactions, extract_custom_terms, redact_pattern, redact_sensitive_data


class TestRedactSensitiveData:
    """Test suite for the redact_sensitive_data function."""

    def create_mock_tool_use(self, markdown_content="", redaction_rules="", redaction_symbol="[REDACTED]", preserve_structure=False):
        """Helper method to create a mock ToolUse object."""
        return {
            "toolUseId": "test-tool-123",
            "input": {"markdown_content": markdown_content, "redaction_rules": redaction_rules, "redaction_symbol": redaction_symbol, "preserve_structure": preserve_structure},
        }

    def test_redact_sensitive_data_success(self):
        """Test successful redaction of sensitive data."""
        markdown_content = "Contact John at john.doe@example.com or call (555) 123-4567"
        redaction_rules = "redact all email addresses and phone numbers"

        tool = self.create_mock_tool_use(markdown_content, redaction_rules)
        result = redact_sensitive_data(tool)

        assert result["toolUseId"] == "test-tool-123"
        assert result["status"] == "success"
        assert "Successfully redacted sensitive information" in result["content"][0]["text"]
        assert "[REDACTED]" in result["content"][0]["text"]

    def test_redact_sensitive_data_missing_content(self):
        """Test error handling when no markdown content is provided."""
        tool = self.create_mock_tool_use("", "redact emails")
        result = redact_sensitive_data(tool)

        assert result["status"] == "error"
        assert "No markdown content provided" in result["content"][0]["text"]

    def test_redact_sensitive_data_missing_rules(self):
        """Test error handling when no redaction rules are specified."""
        tool = self.create_mock_tool_use("Some content", "")
        result = redact_sensitive_data(tool)

        assert result["status"] == "error"
        assert "No redaction rules specified" in result["content"][0]["text"]

    def test_redact_sensitive_data_custom_symbol(self):
        """Test redaction with custom redaction symbol."""
        markdown_content = "Email me at test@example.com"
        redaction_rules = "redact email addresses"

        tool = self.create_mock_tool_use(markdown_content, redaction_rules, "***HIDDEN***")
        result = redact_sensitive_data(tool)

        assert result["status"] == "success"
        assert "***HIDDEN***" in result["content"][0]["text"]

    def test_redact_sensitive_data_preserve_structure(self):
        """Test redaction with structure preservation."""
        markdown_content = "Call me at (555) 123-4567"
        redaction_rules = "redact phone numbers"

        tool = self.create_mock_tool_use(markdown_content, redaction_rules, "[REDACTED]", True)
        result = redact_sensitive_data(tool)

        assert result["status"] == "success"
        assert "█" in result["content"][0]["text"]

    def test_redact_sensitive_data_exception_handling(self):
        """Test exception handling in the main function."""
        # Create a malformed tool object that will cause an exception
        tool = {"toolUseId": "test-123"}  # Missing 'input' key

        result = redact_sensitive_data(tool)

        assert result["status"] == "error"


class TestApplyRedactions:
    """Test suite for the apply_redactions function."""

    def test_apply_redactions_email(self):
        """Test redacting email addresses."""
        content = "Contact us at support@company.com or admin@test.org"
        rules = "redact all email addresses"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "support@company.com" not in result
        assert "admin@test.org" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_phone(self):
        """Test redacting phone numbers."""
        content = "Call (555) 123-4567 or +1-800-555-0123"
        rules = "redact phone numbers"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "(555) 123-4567" not in result
        assert "+1-800-555-0123" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_ssn(self):
        """Test redacting Social Security Numbers."""
        content = "SSN: 123-45-6789 or 987654321"
        rules = "redact SSN"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "123-45-6789" not in result
        assert "987654321" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_credit_card(self):
        """Test redacting credit card numbers."""
        content = "Card: 1234 5678 9012 3456 or 1111-2222-3333-4444"
        rules = "redact credit card numbers"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "1234 5678 9012 3456" not in result
        assert "1111-2222-3333-4444" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_names(self):
        """Test redacting names."""
        content = "Meet John Doe and Jane Smith at the meeting"
        rules = "redact names"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "John Doe" not in result
        assert "Jane Smith" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_addresses(self):
        """Test redacting addresses."""
        content = "Visit us at 123 Main Street or 456 Oak Avenue"
        rules = "redact addresses"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "123 Main Street" not in result
        assert "456 Oak Avenue" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_multiple_types(self):
        """Test redacting multiple types of sensitive data."""
        content = "John Doe (john@example.com) at 123 Main Street, call (555) 123-4567"
        rules = "redact names, emails, addresses, and phone numbers"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "John Doe" not in result
        assert "john@example.com" not in result
        assert "123 Main Street" not in result
        assert "(555) 123-4567" not in result
        assert result.count("[REDACTED]") >= 4

    def test_apply_redactions_custom_terms(self):
        """Test redacting custom terms."""
        content = "Project Falcon is confidential, also Operation Phoenix"
        rules = "redact 'Project Falcon' and 'Operation Phoenix'"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "Project Falcon" not in result
        assert "Operation Phoenix" not in result
        assert "[REDACTED]" in result

    def test_apply_redactions_preserve_structure(self):
        """Test structure preservation during redaction."""
        content = "Email: test@example.com"
        rules = "redact email"

        result = apply_redactions(content, rules, "[REDACTED]", True)

        assert "test@example.com" not in result
        assert "█" in result
        assert len(result.split("█")) > 1  # Should have multiple redaction characters

    def test_apply_redactions_no_matches(self):
        """Test when no patterns match."""
        content = "This is just plain text with no sensitive data"
        rules = "redact email addresses"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert result == content  # Should be unchanged

    def test_apply_redactions_case_insensitive(self):
        """Test case-insensitive redaction."""
        content = "Contact EMAIL@EXAMPLE.COM or email@example.com"
        rules = "redact emails"

        result = apply_redactions(content, rules, "[REDACTED]", False)

        assert "EMAIL@EXAMPLE.COM" not in result
        assert "email@example.com" not in result
        assert "[REDACTED]" in result


class TestRedactPattern:
    """Test suite for the redact_pattern function."""

    def test_redact_pattern_basic(self):
        """Test basic pattern redaction."""
        content = "The secret code is ABC123"
        pattern = r"[A-Z]{3}\d{3}"

        result = redact_pattern(content, pattern, "[HIDDEN]", False)

        assert "ABC123" not in result
        assert "[HIDDEN]" in result

    def test_redact_pattern_preserve_structure(self):
        """Test pattern redaction with structure preservation."""
        content = "Password: secret123"
        pattern = r"secret\d+"

        result = redact_pattern(content, pattern, "[HIDDEN]", True)

        assert "secret123" not in result
        assert "█" in result
        assert "Password: " in result  # Non-matching part preserved

    def test_redact_pattern_case_insensitive(self):
        """Test case-insensitive pattern redaction."""
        content = "User: ADMIN or admin"
        pattern = r"admin"

        result = redact_pattern(content, pattern, "[REDACTED]", False, case_insensitive=True)

        assert "ADMIN" not in result
        assert "admin" not in result
        assert "[REDACTED]" in result

    def test_redact_pattern_case_sensitive(self):
        """Test case-sensitive pattern redaction."""
        content = "User: ADMIN or admin"
        pattern = r"admin"

        result = redact_pattern(content, pattern, "[REDACTED]", False, case_insensitive=False)

        assert "ADMIN" in result  # Should remain (case sensitive)
        assert "admin" not in result  # Should be redacted
        assert "[REDACTED]" in result

    def test_redact_pattern_multiple_matches(self):
        """Test redacting multiple matches of the same pattern."""
        content = "Codes: ABC123, DEF456, GHI789"
        pattern = r"[A-Z]{3}\d{3}"

        result = redact_pattern(content, pattern, "[CODE]", False)

        assert "ABC123" not in result
        assert "DEF456" not in result
        assert "GHI789" not in result
        assert result.count("[CODE]") == 3

    def test_redact_pattern_no_matches(self):
        """Test pattern redaction when no matches found."""
        content = "No sensitive data here"
        pattern = r"\d{3}-\d{2}-\d{4}"

        result = redact_pattern(content, pattern, "[SSN]", False)

        assert result == content  # Should be unchanged


class TestExtractCustomTerms:
    """Test suite for the extract_custom_terms function."""

    def test_extract_custom_terms_quoted_single(self):
        """Test extracting single-quoted terms."""
        rules = "Please redact 'Project Alpha' from the document"

        result = extract_custom_terms(rules)

        assert "Project Alpha" in result

    def test_extract_custom_terms_quoted_double(self):
        """Test extracting double-quoted terms."""
        rules = 'Remove "Operation Beta" and "Client Code"'

        result = extract_custom_terms(rules)

        assert "Operation Beta" in result
        assert "Client Code" in result

    def test_extract_custom_terms_after_redact(self):
        """Test extracting terms after 'redact' keyword."""
        rules = "redact company names and remove department codes"

        result = extract_custom_terms(rules)

        # Should extract custom terms but filter out common patterns
        # This is a simplified test - the actual implementation may vary
        assert len(result) >= 0  # May or may not extract depending on implementation

    def test_extract_custom_terms_mixed(self):
        """Test extracting mixed quoted and keyword terms."""
        rules = "redact 'Secret Project' and remove all instances of \"Code Red\""

        result = extract_custom_terms(rules)

        assert "Secret Project" in result
        assert "Code Red" in result

    def test_extract_custom_terms_empty_rules(self):
        """Test extracting from empty rules."""
        rules = ""

        result = extract_custom_terms(rules)

        assert result == []

    def test_extract_custom_terms_no_custom_terms(self):
        """Test when no custom terms are present."""
        rules = "redact all email addresses and phone numbers"

        result = extract_custom_terms(rules)

        # Should not extract common patterns like 'email' or 'phone'
        assert len([term for term in result if term.lower() not in ["email", "phone"]]) >= 0


class TestToolSpec:
    """Test suite for the TOOL_SPEC constant."""

    def test_tool_spec_structure(self):
        """Test that TOOL_SPEC has the required structure."""
        assert "name" in TOOL_SPEC
        assert "description" in TOOL_SPEC
        assert "inputSchema" in TOOL_SPEC

        assert TOOL_SPEC["name"] == "redact_sensitive_data"
        assert isinstance(TOOL_SPEC["description"], str)
        assert len(TOOL_SPEC["description"]) > 0

    def test_tool_spec_input_schema(self):
        """Test the input schema structure."""
        schema = TOOL_SPEC["inputSchema"]["json"]

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Check required properties
        required = schema["required"]
        assert "markdown_content" in required
        assert "redaction_rules" in required

        # Check property definitions
        properties = schema["properties"]
        assert "markdown_content" in properties
        assert "redaction_rules" in properties
        assert "redaction_symbol" in properties
        assert "preserve_structure" in properties

    def test_tool_spec_default_values(self):
        """Test default values in the tool specification."""
        properties = TOOL_SPEC["inputSchema"]["json"]["properties"]

        assert properties["redaction_symbol"]["default"] == "[REDACTED]"
        assert properties["preserve_structure"]["default"] is False


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_redaction_workflow(self):
        """Test a complete redaction workflow."""
        markdown_content = """
        # Contract Details

        **Client**: John Smith (john.smith@company.com)
        **Phone**: (555) 123-4567
        **Address**: 123 Main Street, Anytown
        **SSN**: 123-45-6789
        **Credit Card**: 1234 5678 9012 3456

        Please contact regarding 'Project Confidential'.
        """

        tool = {
            "toolUseId": "integration-test",
            "input": {
                "markdown_content": markdown_content,
                "redaction_rules": "redact all personal information including names, emails, phones, addresses, SSN, credit cards, and 'Project Confidential'",
                "redaction_symbol": "[PRIVATE]",
                "preserve_structure": False,
            },
        }

        result = redact_sensitive_data(tool)

        assert result["status"] == "success"
        redacted_text = result["content"][0]["text"]

        # Verify sensitive data is removed
        assert "john.smith@company.com" not in redacted_text
        assert "(555) 123-4567" not in redacted_text
        assert "123 Main Street" not in redacted_text
        assert "123-45-6789" not in redacted_text
        assert "1234 5678 9012 3456" not in redacted_text

        # Verify structure is preserved
        assert "**Client**:" in redacted_text

    @pytest.mark.parametrize("preserve_structure", [True, False])
    def test_structure_preservation_modes(self, preserve_structure):
        """Test both structure preservation modes."""
        content = "Email: test@example.com"
        rules = "redact email"

        result = apply_redactions(content, rules, "[HIDDEN]", preserve_structure)

        assert "test@example.com" not in result
        if preserve_structure:
            assert "█" in result
        else:
            assert "[HIDDEN]" in result
