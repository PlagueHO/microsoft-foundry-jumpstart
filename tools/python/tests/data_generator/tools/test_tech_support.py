"""
Unit tests for the data_generator.tools.tech_support module.
"""

import argparse
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Import the module we want to test
from data_generator.tools.tech_support import TechSupportTool


@pytest.fixture
def tech_support_tool():
    """Return a basic TechSupportTool instance for testing."""
    return TechSupportTool()


@pytest.fixture
def tech_support_with_desc():
    """Return a TechSupportTool instance with custom system description."""
    return TechSupportTool(system_description="Test System Description")


def test_init_default():
    """Test initialization with default parameters."""
    tool = TechSupportTool()
    assert tool.system_description == "A generic SaaS platform running in Azure."


def test_init_custom_description():
    """Test initialization with custom system description."""
    custom_desc = "Custom Test System"
    tool = TechSupportTool(system_description=custom_desc)
    assert tool.system_description == custom_desc


def test_cli_arguments(tech_support_tool):
    """Test cli_arguments returns the expected structure."""
    args = tech_support_tool.cli_arguments()
    assert isinstance(args, list)
    assert len(args) == 1
    assert "flags" in args[0]
    assert "-d" in args[0]["flags"]
    assert "--system-description" in args[0]["flags"]
    assert "kwargs" in args[0]
    assert args[0]["kwargs"]["required"] is True


def test_validate_args_valid():
    """Test validate_args with valid arguments."""
    tool = TechSupportTool()
    ns = argparse.Namespace(system_description="Valid Description")
    tool.validate_args(ns)
    assert tool.system_description == "Valid Description"


def test_validate_args_missing():
    """Test validate_args raises error when system_description is missing."""
    tool = TechSupportTool()
    ns = argparse.Namespace()
    with pytest.raises(ValueError, match="--system-description is required"):
        tool.validate_args(ns)


def test_examples(tech_support_tool):
    """Test examples returns non-empty list of valid examples."""
    examples = tech_support_tool.examples()
    assert isinstance(examples, list)
    assert len(examples) > 0
    assert all(isinstance(ex, str) for ex in examples)
    assert all("--scenario tech-support" in ex for ex in examples)


def test_supported_output_formats(tech_support_tool):
    """Test supported_output_formats returns expected formats."""
    formats = tech_support_tool.supported_output_formats()
    assert isinstance(formats, list)
    assert set(formats) == {"yaml", "json", "txt"}


@patch("data_generator.tools.tech_support.random.choice")
def test_random_attributes(mock_choice, tech_support_tool):
    """Test _random_attributes returns expected values."""
    # Configure mock to return fixed values
    mock_choice.side_effect = ["open", "medium", "P2"]

    status, severity, priority = tech_support_tool._random_attributes()
    
    assert status == "open"
    assert severity == "medium"
    assert priority == "P2"
    assert mock_choice.call_count == 3


@patch("uuid.uuid4")
@patch("data_generator.tools.tech_support.datetime")
@patch("data_generator.tools.tech_support.TechSupportTool._random_attributes")
def test_prompt_common(mock_attrs, mock_datetime, mock_uuid, tech_support_tool):
    """Test _prompt_common returns correctly formatted string."""
    # Configure mocks
    mock_attrs.return_value = ("open", "high", "P1")
    mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
    mock_dt = MagicMock()
    mock_dt.now.return_value = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_dt.isoformat.return_value = "2023-01-01T12:00:00+00:00"
    mock_datetime.now.return_value = mock_dt

    # Test without unique_id
    result = tech_support_tool._prompt_common()
    assert "The status of this case is: open" in result
    assert "The severity of this case is: high" in result
    assert "The priority of this case is: P1" in result
    assert "Case ID (immutable): 12345678-1234-5678-1234-567812345678" in result
    
    # Test with unique_id
    result = tech_support_tool._prompt_common(unique_id="test-id-123")
    assert "Case ID (immutable): test-id-123" in result


def test_build_prompt_yaml(tech_support_tool):
    """Test build_prompt for YAML format."""
    result = tech_support_tool.build_prompt("yaml", unique_id="test-id")
    assert "Return VALID YAML ONLY (no markdown fences)" in result
    assert "case_id: (echo above)" in result
    assert "The system being simulated" in result


def test_build_prompt_json(tech_support_tool):
    """Test build_prompt for JSON format."""
    result = tech_support_tool.build_prompt("json", unique_id="test-id")
    assert "Return VALID JSON ONLY (no markdown fences)" in result
    assert '"case_id": "(echo above)"' in result
    assert "The system being simulated" in result


def test_build_prompt_text(tech_support_tool):
    """Test build_prompt for text format."""
    result = tech_support_tool.build_prompt("txt", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Case ID: (echo above)" in result
    assert "The system being simulated" in result


def test_yaml_skeleton():
    """Test _yaml_skeleton returns expected YAML template."""
    result = TechSupportTool._yaml_skeleton()
    assert "Return VALID YAML ONLY" in result
    assert "case_id: (echo above)" in result
    assert "conversation_history:" in result


def test_json_skeleton():
    """Test _json_skeleton returns expected JSON template."""
    result = TechSupportTool._json_skeleton()
    assert "Return VALID JSON ONLY" in result
    assert '"case_id": "(echo above)"' in result
    assert '"conversation_history": [' in result


def test_text_skeleton():
    """Test _text_skeleton returns expected text template."""
    result = TechSupportTool._text_skeleton()
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Case ID: (echo above)" in result
    assert "Conversation History:" in result


def test_post_process_json_valid():
    """Test post_process with valid JSON."""
    tool = TechSupportTool()
    valid_json = '{"key": "value", "nested": {"list": [1, 2, 3]}}'
    result = tool.post_process(valid_json, "json")
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["nested"]["list"] == [1, 2, 3]


def test_post_process_json_invalid():
    """Test post_process with invalid JSON returns raw string."""
    tool = TechSupportTool()
    invalid_json = '{"key": "value", unclosed_bracket'
    result = tool.post_process(invalid_json, "json")
    assert result == invalid_json


def test_post_process_yaml_valid():
    """Test post_process with valid YAML."""
    tool = TechSupportTool()
    valid_yaml = "key: value\nnested:\n  list:\n    - 1\n    - 2\n    - 3"
    result = tool.post_process(valid_yaml, "yaml")
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["nested"]["list"] == [1, 2, 3]


def test_post_process_yaml_invalid():
    """Test post_process with invalid YAML returns raw string."""
    tool = TechSupportTool()
    invalid_yaml = "key: value\ninvalid:\n  - missing colon\n  item"
    result = tool.post_process(invalid_yaml, "yaml")
    assert result == invalid_yaml


def test_post_process_text():
    """Test post_process with text format returns raw string."""
    tool = TechSupportTool()
    text = "This is plain text content"
    result = tool.post_process(text, "txt")
    assert result == text


def test_get_system_description(tech_support_with_desc):
    """Test get_system_description returns the correct value."""
    assert tech_support_with_desc.get_system_description() == "Test System Description"