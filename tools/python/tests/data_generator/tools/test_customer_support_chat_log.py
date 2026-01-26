"""
Unit tests for the data_generator.tools.customer_support_chat_log module.
"""

import argparse
import uuid
from unittest.mock import MagicMock, patch

import pytest

# Import the module we want to test
from data_generator.tools.customer_support_chat_log import CustomerSupportChatLogTool


@pytest.fixture
def customer_support_tool():
    """Return a basic CustomerSupportChatLogTool instance for testing."""
    return CustomerSupportChatLogTool()


@pytest.fixture
def customer_support_custom():
    """Return a CustomerSupportChatLogTool instance with custom parameters."""
    return CustomerSupportChatLogTool(
        industry="telecom",
        avg_turns=12,
        languages="en,es"
    )


class TestCustomerSupportChatLogTool:
    """Test suite for CustomerSupportChatLogTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_init_defaults(self):
        """Test initialization with default parameters."""
        tool = CustomerSupportChatLogTool()
        assert tool.industry == "general"
        assert tool.avg_turns == 8
        assert tool.languages == "en"

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        tool = CustomerSupportChatLogTool(
            industry="banking",
            avg_turns=15,
            languages="en,fr,de"
        )
        assert tool.industry == "banking"
        assert tool.avg_turns == 15
        assert tool.languages == "en,fr,de"

    def test_class_attributes(self):
        """Test class attributes are correctly set."""
        tool = CustomerSupportChatLogTool()
        assert tool.name == "customer-support-chat-log"
        assert tool.toolName == "CustomerSupportChatLog"

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self, customer_support_tool):
        """Test cli_arguments returns the expected structure."""
        args = customer_support_tool.cli_arguments()
        assert isinstance(args, list)
        assert len(args) == 3

        # Check industry argument
        industry_arg = next((arg for arg in args if "--industry" in arg["flags"]), None)
        assert industry_arg is not None
        assert not industry_arg["kwargs"]["required"]
        assert industry_arg["kwargs"]["default"] == "general"

        # Check avg-turns argument
        avg_turns_arg = next(
            (arg for arg in args if "--avg-turns" in arg["flags"]), None
        )
        assert avg_turns_arg is not None
        assert avg_turns_arg["kwargs"]["type"] is int
        assert avg_turns_arg["kwargs"]["default"] == 8

        # Check languages argument
        languages_arg = next(
            (arg for arg in args if "--languages" in arg["flags"]), None
        )
        assert languages_arg is not None
        assert not languages_arg["kwargs"]["required"]
        assert languages_arg["kwargs"]["default"] == "en"

    def test_validate_args_defaults(self):
        """Test validate_args with default values."""
        tool = CustomerSupportChatLogTool()
        ns = argparse.Namespace()
        tool.validate_args(ns)
        assert tool.industry == "general"
        assert tool.avg_turns == 8
        assert tool.languages == "en"

    def test_validate_args_custom_values(self):
        """Test validate_args with custom values."""
        tool = CustomerSupportChatLogTool()
        ns = argparse.Namespace(
            industry="retail",
            avg_turns=10,
            languages="en,es,fr"
        )
        tool.validate_args(ns)
        assert tool.industry == "retail"
        assert tool.avg_turns == 10
        assert tool.languages == "en,es,fr"

    def test_validate_args_clamping(self):
        """Test validate_args clamps avg_turns to valid range."""
        tool = CustomerSupportChatLogTool()

        # Test lower bound
        ns = argparse.Namespace(avg_turns=1)
        tool.validate_args(ns)
        assert tool.avg_turns == 2

        # Test upper bound
        ns = argparse.Namespace(avg_turns=100)
        tool.validate_args(ns)
        assert tool.avg_turns == 50

        # Test valid range
        ns = argparse.Namespace(avg_turns=25)
        tool.validate_args(ns)
        assert tool.avg_turns == 25

    def test_validate_args_invalid_avg_turns(self):
        """Test validate_args handles invalid avg_turns gracefully."""
        tool = CustomerSupportChatLogTool()

        # Test string that can't be converted
        ns = argparse.Namespace(avg_turns="invalid")
        tool.validate_args(ns)
        assert tool.avg_turns == 8  # Should default to 8

        # Test None
        ns = argparse.Namespace(avg_turns=None)
        tool.validate_args(ns)
        assert tool.avg_turns == 8

    def test_examples(self, customer_support_tool):
        """Test examples returns non-empty list of valid examples."""
        examples = customer_support_tool.examples()
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("--scenario customer-support-chat-log" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self, customer_support_tool):
        """Test supported_output_formats returns expected formats."""
        formats = customer_support_tool.supported_output_formats()
        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "text"}

    # ------------------------------------------------------------------ #
    # Helper Method Tests                                                #
    # ------------------------------------------------------------------ #
    def test_random_channel(self, customer_support_tool):
        """Test _random_channel returns valid channel."""
        channel = customer_support_tool._random_channel()
        assert channel in customer_support_tool._CHANNELS
        assert channel in ["email", "chat", "phone"]

    def test_random_resolution_status(self, customer_support_tool):
        """Test _random_resolution_status returns valid status."""
        status = customer_support_tool._random_resolution_status()
        assert status in customer_support_tool._RESOLUTION_STATUS
        assert status in ["open", "in_progress", "resolved", "escalated"]

    def test_select_language_single(self):
        """Test _select_language with single language."""
        tool = CustomerSupportChatLogTool(languages="fr")
        lang = tool._select_language()
        assert lang == "fr"

    def test_select_language_multiple(self):
        """Test _select_language with multiple languages."""
        tool = CustomerSupportChatLogTool(languages="en,es,fr")
        lang = tool._select_language()
        assert lang in ["en", "es", "fr"]

    def test_select_language_with_spaces(self):
        """Test _select_language handles spaces in language list."""
        tool = CustomerSupportChatLogTool(languages="en, es, fr")
        lang = tool._select_language()
        assert lang in ["en", "es", "fr"]

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    @patch("uuid.uuid4")
    @patch("data_generator.tools.customer_support_chat_log.datetime")
    def test_prompt_common(self, mock_datetime, mock_uuid, customer_support_tool):
        """Test _prompt_common returns correctly formatted string."""
        # Configure mocks
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_dt_instance = MagicMock()
        mock_dt_instance.isoformat.return_value = "2023-01-01T12:00:00+00:00"
        mock_datetime.now.return_value = mock_dt_instance

        # Test without unique_id
        result = customer_support_tool._prompt_common()
        assert (
            "Conversation ID (immutable): 12345678-1234-5678-1234-567812345678"
            in result
        )
        assert "Created At: 2023-01-01T12:00:00+00:00" in result
        assert "Industry: general" in result
        assert "Language: en" in result
        assert "Average Turns Hint: 8" in result

        # Test with unique_id
        result = customer_support_tool._prompt_common(unique_id="test-conv-123")
        assert "Conversation ID (immutable): test-conv-123" in result

    def test_build_prompt_yaml(self, customer_support_tool):
        """Test build_prompt for YAML format."""
        result = customer_support_tool.build_prompt("yaml", unique_id="test-id")
        assert "Return VALID YAML ONLY (no markdown fences)" in result
        assert "conversation_id: (echo above)" in result
        assert "CONVERSATION DETAILS" in result
        assert "multi-turn customer support chat logs" in result

    def test_build_prompt_json(self, customer_support_tool):
        """Test build_prompt for JSON format."""
        result = customer_support_tool.build_prompt("json", unique_id="test-id")
        assert "Return VALID JSON ONLY (no markdown fences)" in result
        assert '"conversation_id": "(echo above)"' in result
        assert "CONVERSATION DETAILS" in result
        assert "multi-turn customer support chat logs" in result

    def test_build_prompt_text(self, customer_support_tool):
        """Test build_prompt for text format."""
        result = customer_support_tool.build_prompt("text", unique_id="test-id")
        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
        assert "Conversation ID: (echo above)" in result
        assert "CONVERSATION DETAILS" in result
        assert "multi-turn customer support chat logs" in result

    def test_build_prompt_unknown_format(self, customer_support_tool):
        """Test build_prompt with unknown format defaults to text."""
        result = customer_support_tool.build_prompt("unknown", unique_id="test-id")
        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result

    # ------------------------------------------------------------------ #
    # Skeleton Method Tests                                              #
    # ------------------------------------------------------------------ #
    def test_yaml_skeleton(self, customer_support_tool):
        """Test _yaml_skeleton returns expected YAML template."""
        result = customer_support_tool._yaml_skeleton()
        assert "Return VALID YAML ONLY" in result
        assert "conversation_id: (echo above)" in result
        assert "customer_profile:" in result
        assert "messages:" in result
        assert "resolution_status:" in result

    def test_json_skeleton(self, customer_support_tool):
        """Test _json_skeleton returns expected JSON template."""
        result = customer_support_tool._json_skeleton()
        assert "Return VALID JSON ONLY" in result
        assert '"conversation_id": "(echo above)"' in result
        assert '"customer_profile": {' in result
        assert '"messages": [' in result
        assert '"resolution_status":' in result

    def test_text_skeleton(self, customer_support_tool):
        """Test _text_skeleton returns expected text template."""
        result = customer_support_tool._text_skeleton()
        assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
        assert "Conversation ID: (echo above)" in result
        assert "Customer Profile:" in result
        assert "Conversation History:" in result
        assert "Resolution Status:" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self, customer_support_tool):
        """Test post_process with valid JSON."""
        valid_json = '{"conversation_id": "123", "industry": "tech"}'
        result = customer_support_tool.post_process(valid_json, "json")
        assert isinstance(result, dict)
        assert result["conversation_id"] == "123"
        assert result["industry"] == "tech"
        assert "resolution_status" in result  # Check enrichment

    def test_post_process_json_invalid(self, customer_support_tool):
        """Test post_process with invalid JSON returns raw string."""
        invalid_json = '{"conversation_id": "123", unclosed_bracket'
        result = customer_support_tool.post_process(invalid_json, "json")
        assert result == invalid_json

    def test_post_process_yaml_valid(self, customer_support_tool):
        """Test post_process with valid YAML."""
        valid_yaml = "conversation_id: 123\nindustry: tech"
        result = customer_support_tool.post_process(valid_yaml, "yaml")
        assert isinstance(result, dict)
        assert result["conversation_id"] == 123
        assert result["industry"] == "tech"
        assert "resolution_status" in result  # Check enrichment

    def test_post_process_yaml_invalid(self, customer_support_tool):
        """Test post_process with invalid YAML returns raw string."""
        invalid_yaml = "conversation_id: 123\ninvalid:\n  - missing colon\n  item"
        result = customer_support_tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml

    def test_post_process_text(self, customer_support_tool):
        """Test post_process with text format returns raw string."""
        text = "This is plain text conversation log"
        result = customer_support_tool.post_process(text, "text")
        assert result == text

        # Also test with "txt" format alias
        result = customer_support_tool.post_process(text, "txt")
        assert result == text

    def test_post_process_unknown_format(self, customer_support_tool):
        """Test post_process with unknown format returns raw string."""
        data = "Some conversation data"
        result = customer_support_tool.post_process(data, "unknown_format")
        assert result == data

    # ------------------------------------------------------------------ #
    # System Description Tests                                           #
    # ------------------------------------------------------------------ #
    def test_get_system_description_default(self, customer_support_tool):
        """Test get_system_description with default parameters."""
        result = customer_support_tool.get_system_description()
        assert result == "Customer support chat logs for general (languages: en)"

    def test_get_system_description_custom(self, customer_support_custom):
        """Test get_system_description with custom parameters."""
        result = customer_support_custom.get_system_description()
        assert result == "Customer support chat logs for telecom (languages: en, es)"

    def test_get_system_description_multiple_languages(self):
        """Test get_system_description formats multiple languages correctly."""
        tool = CustomerSupportChatLogTool(
            industry="banking",
            languages="en,fr,de,es"
        )
        result = tool.get_system_description()
        assert result == (
            "Customer support chat logs for banking (languages: en, fr, de, es)"
        )

    # ------------------------------------------------------------------ #
    # Data Enrichment Tests                                              #
    # ------------------------------------------------------------------ #
    def test_json_enrichment_adds_resolution_status(self, customer_support_tool):
        """Test JSON post-processing adds resolution_status if missing."""
        minimal_json = '{"conversation_id": "123", "industry": "tech"}'
        result = customer_support_tool.post_process(minimal_json, "json")
        assert "resolution_status" in result
        assert result["resolution_status"] in (
            customer_support_tool._RESOLUTION_STATUS
        )

    def test_yaml_enrichment_adds_resolution_status(self, customer_support_tool):
        """Test YAML post-processing adds resolution_status if missing."""
        minimal_yaml = "conversation_id: 123\nindustry: tech"
        result = customer_support_tool.post_process(minimal_yaml, "yaml")
        assert "resolution_status" in result
        assert result["resolution_status"] in (
            customer_support_tool._RESOLUTION_STATUS
        )

    def test_enrichment_preserves_existing_resolution_status(
        self, customer_support_tool
    ):
        """Test enrichment preserves existing resolution_status."""
        json_with_status = '{"conversation_id": "123", "resolution_status": "resolved"}'
        result = customer_support_tool.post_process(json_with_status, "json")
        assert result["resolution_status"] == "resolved"

    def test_enrichment_only_for_dict_objects(self, customer_support_tool):
        """Test enrichment only applies to dictionary objects."""
        list_yaml = "- item1\n- item2"
        result = customer_support_tool.post_process(list_yaml, "yaml")
        assert isinstance(result, list)
        # No enrichment should occur for non-dict objects
