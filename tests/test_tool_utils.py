import json

import pytest

from doc_redaction.tool.tool_utils import omit_empty_keys


class TestOmitEmptyKeys:
    """Test suite for the omit_empty_keys function."""

    def test_omit_empty_keys_with_mixed_data(self):
        """Test filtering a JSON object with both empty and non-empty values."""
        input_json = json.dumps({"names": ["John Doe", "Jane Smith"], "emails": [], "phones": ["123-456-7890"], "addresses": []})

        result = omit_empty_keys(input_json)

        expected = {"names": ["John Doe", "Jane Smith"], "phones": ["123-456-7890"]}
        assert result == expected

    def test_omit_empty_keys_all_empty_lists(self):
        """Test with JSON containing only empty lists."""
        input_json = json.dumps({"field1": [], "field2": [], "field3": []})

        result = omit_empty_keys(input_json)

        assert result == {}

    def test_omit_empty_keys_all_non_empty_lists(self):
        """Test with JSON containing only non-empty lists."""
        input_json = json.dumps({"companies": ["Company A", "Company B"], "contacts": ["contact1@example.com"], "departments": ["HR", "IT", "Finance"]})

        result = omit_empty_keys(input_json)

        expected = {"companies": ["Company A", "Company B"], "contacts": ["contact1@example.com"], "departments": ["HR", "IT", "Finance"]}
        assert result == expected

    def test_omit_empty_keys_empty_json_object(self):
        """Test with an empty JSON object."""
        input_json = json.dumps({})

        result = omit_empty_keys(input_json)

        assert result == {}

    def test_omit_empty_keys_single_empty_list(self):
        """Test with a single empty list."""
        input_json = json.dumps({"empty_field": []})

        result = omit_empty_keys(input_json)

        assert result == {}

    def test_omit_empty_keys_single_non_empty_list(self):
        """Test with a single non-empty list."""
        input_json = json.dumps({"data": ["value1", "value2"]})

        result = omit_empty_keys(input_json)

        assert result == {"data": ["value1", "value2"]}

    def test_omit_empty_keys_filters_none_values(self):
        """Test that None values are also filtered out."""
        input_json = json.dumps({"valid_data": ["item1", "item2"], "null_data": None, "empty_data": []})

        result = omit_empty_keys(input_json)

        assert result == {"valid_data": ["item1", "item2"]}

    def test_omit_empty_keys_filters_false_values(self):
        """Test that False values are filtered out (falsy)."""
        input_json = json.dumps({"valid_data": ["item1"], "false_data": False, "empty_data": []})

        result = omit_empty_keys(input_json)

        assert result == {"valid_data": ["item1"]}

    def test_omit_empty_keys_keeps_zero_in_list(self):
        """Test that lists containing zero are kept (truthy list)."""
        input_json = json.dumps({"numbers": [0, 1, 2], "empty_numbers": []})

        result = omit_empty_keys(input_json)

        assert result == {"numbers": [0, 1, 2]}

    def test_omit_empty_keys_keeps_false_in_list(self):
        """Test that lists containing False are kept (truthy list)."""
        input_json = json.dumps({"booleans": [False, True], "empty_booleans": []})

        result = omit_empty_keys(input_json)

        assert result == {"booleans": [False, True]}

    def test_omit_empty_keys_with_string_values(self):
        """Test with string values instead of lists."""
        input_json = json.dumps({"name": "John Doe", "email": "", "phone": "123-456-7890", "address": ""})

        result = omit_empty_keys(input_json)

        expected = {"name": "John Doe", "phone": "123-456-7890"}
        assert result == expected

    def test_omit_empty_keys_with_mixed_types(self):
        """Test with mixed data types (lists, strings, numbers)."""
        input_json = json.dumps({"names": ["John", "Jane"], "count": 5, "empty_list": [], "empty_string": "", "valid_string": "test", "zero": 0})

        result = omit_empty_keys(input_json)

        expected = {"names": ["John", "Jane"], "count": 5, "valid_string": "test"}
        assert result == expected

    def test_omit_empty_keys_invalid_json_raises_error(self):
        """Test that invalid JSON raises JSONDecodeError."""
        invalid_json = "{'invalid': 'json'}"  # Single quotes are not valid JSON

        with pytest.raises(json.JSONDecodeError):
            omit_empty_keys(invalid_json)

    def test_omit_empty_keys_malformed_json_raises_error(self):
        """Test that malformed JSON raises JSONDecodeError."""
        malformed_json = '{"incomplete": "object"'  # Missing closing brace

        with pytest.raises(json.JSONDecodeError):
            omit_empty_keys(malformed_json)

    def test_omit_empty_keys_non_object_json_raises_error(self):
        """Test that non-object JSON (like arrays) raises appropriate error."""
        array_json = '["not", "an", "object"]'

        with pytest.raises(AttributeError):  # .items() not available on lists
            omit_empty_keys(array_json)

    def test_omit_empty_keys_preserves_list_order(self):
        """Test that the order of items in lists is preserved."""
        input_json = json.dumps({"ordered_list": ["first", "second", "third"], "empty_list": []})

        result = omit_empty_keys(input_json)

        assert result["ordered_list"] == ["first", "second", "third"]

    def test_omit_empty_keys_real_world_example(self):
        """Test with a realistic example from document processing."""
        input_json = json.dumps({
            "people_names": ["John Smith", "Jane Doe"],
            "email_addresses": [],
            "phone_numbers": ["+1-555-0123"],
            "company_names": ["Acme Corp"],
            "addresses": [],
            "registration_numbers": [],
            "contract_dates": ["2024-01-15"],
        })

        result = omit_empty_keys(input_json)

        expected = {"people_names": ["John Smith", "Jane Doe"], "phone_numbers": ["+1-555-0123"], "company_names": ["Acme Corp"], "contract_dates": ["2024-01-15"]}
        assert result == expected

    @pytest.mark.parametrize("empty_value", [[], "", None, False, 0])
    def test_omit_empty_keys_filters_falsy_values_parametrized(self, empty_value):
        """Parametrized test for various falsy values."""
        input_json = json.dumps({"valid_data": ["item"], "falsy_data": empty_value})

        result = omit_empty_keys(input_json)

        assert result == {"valid_data": ["item"]}

    def test_omit_empty_keys_return_type(self):
        """Test that the return type is dict[str, list[str]] as documented."""
        input_json = json.dumps({"field1": ["value1", "value2"], "field2": []})

        result = omit_empty_keys(input_json)

        assert isinstance(result, dict)
        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, list)

    def test_omit_empty_keys_whitespace_string(self):
        """Test behavior with whitespace-only strings."""
        input_json = json.dumps({"valid": ["data"], "whitespace": "   ", "empty": ""})

        result = omit_empty_keys(input_json)

        # Whitespace string should be kept (truthy)
        expected = {"valid": ["data"], "whitespace": "   "}
        assert result == expected

    def test_omit_empty_keys_unicode_content(self):
        """Test with Unicode content in the JSON."""
        input_json = json.dumps({"unicode_names": ["José García", "北京"], "empty_unicode": [], "unicode_string": "café"})

        result = omit_empty_keys(input_json)

        expected = {"unicode_names": ["José García", "北京"], "unicode_string": "café"}
        assert result == expected
