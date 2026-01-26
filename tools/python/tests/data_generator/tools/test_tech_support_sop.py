"""
Unit tests for the data_generator.tools.tech_support_sop module.
"""

import argparse
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Import the module we want to test
from data_generator.tools.tech_support_sop import TechSupportSOPTool


@pytest.fixture
def sop_tool():
    """Return a basic TechSupportSOPTool instance for testing."""
    return TechSupportSOPTool()


@pytest.fixture
def sop_tool_custom():
    """Return a TechSupportSOPTool instance with custom parameters."""
    return TechSupportSOPTool(
        problem_category="network",
        complexity="complex",
        system_context="Azure cloud environment",
    )


def test_init_default():
    """Test initialization with default parameters."""
    tool = TechSupportSOPTool()
    assert tool.problem_category == "general"
    assert tool.complexity == "medium"
    assert tool.system_context == "Generic enterprise IT environment"


def test_init_custom_parameters():
    """Test initialization with custom parameters."""
    tool = TechSupportSOPTool(
        problem_category="database",
        complexity="simple",
        system_context="On-premises data center",
    )
    assert tool.problem_category == "database"
    assert tool.complexity == "simple"
    assert tool.system_context == "On-premises data center"


def test_cli_arguments(sop_tool):
    """Test cli_arguments returns the expected structure."""
    args = sop_tool.cli_arguments()
    assert isinstance(args, list)
    assert len(args) == 3

    # Check problem-category argument
    category_arg = next(arg for arg in args if "--problem-category" in arg["flags"])
    expected_categories = [
        "general",
        "network",
        "application",
        "authentication",
        "hardware",
        "database",
        "cloud",
        "security",
    ]
    assert category_arg["kwargs"]["choices"] == expected_categories
    assert category_arg["kwargs"]["default"] == "general"

    # Check complexity argument
    complexity_arg = next(arg for arg in args if "--complexity" in arg["flags"])
    assert complexity_arg["kwargs"]["choices"] == ["simple", "medium", "complex"]
    assert complexity_arg["kwargs"]["default"] == "medium"

    # Check system-context argument
    context_arg = next(arg for arg in args if "--system-context" in arg["flags"])
    assert context_arg["kwargs"]["default"] == "Generic enterprise IT environment"


def test_validate_args_valid():
    """Test validate_args with valid arguments."""
    tool = TechSupportSOPTool()
    ns = argparse.Namespace(
        problem_category="application",
        complexity="complex",
        system_context="AWS cloud environment",
    )
    tool.validate_args(ns)
    assert tool.problem_category == "application"
    assert tool.complexity == "complex"
    assert tool.system_context == "AWS cloud environment"


def test_validate_args_defaults():
    """Test validate_args with missing arguments uses defaults."""
    tool = TechSupportSOPTool()
    ns = argparse.Namespace()
    tool.validate_args(ns)
    assert tool.problem_category == "general"
    assert tool.complexity == "medium"
    assert tool.system_context == "Generic enterprise IT environment"


def test_examples(sop_tool):
    """Test examples returns non-empty list of valid examples."""
    examples = sop_tool.examples()
    assert isinstance(examples, list)
    assert len(examples) > 0
    assert all(isinstance(ex, str) for ex in examples)
    assert all("--scenario tech-support-sop" in ex for ex in examples)


def test_supported_output_formats(sop_tool):
    """Test supported_output_formats returns expected formats."""
    formats = sop_tool.supported_output_formats()
    assert isinstance(formats, list)
    assert set(formats) == {"yaml", "json", "txt", "text"}


@patch("data_generator.tools.tech_support_sop.random.choice")
def test_random_attributes(mock_choice, sop_tool):
    """Test _random_attributes returns expected values."""
    # Configure mock to return fixed values
    mock_choice.side_effect = ["high", "approved", "manager"]

    severity, status, approval_level = sop_tool._random_attributes()

    assert severity == "high"
    assert status == "approved"
    assert approval_level == "manager"
    assert mock_choice.call_count == 3


@patch("uuid.uuid4")
@patch("data_generator.tools.tech_support_sop.datetime")
@patch("data_generator.tools.tech_support_sop.random.randint")
@patch("data_generator.tools.tech_support_sop.TechSupportSOPTool._random_attributes")
def test_prompt_common(mock_attrs, mock_randint, mock_datetime, mock_uuid, sop_tool):
    """Test _prompt_common returns correctly formatted string."""
    # Configure mocks
    mock_attrs.return_value = ("critical", "published", "director")
    mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
    mock_randint.return_value = 5
    mock_dt = MagicMock()
    mock_dt.now.return_value = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_dt.isoformat.return_value = "2023-01-01T12:00:00+00:00"
    mock_datetime.now.return_value = mock_dt

    # Test without unique_id
    result = sop_tool._prompt_common()
    assert "SOP ID (immutable): 12345678-1234-5678-1234-567812345678" in result
    assert "Version: 1.5" in result
    assert "Problem Category: general" in result
    assert "Complexity: medium" in result
    assert "System Context: Generic enterprise IT environment" in result
    assert "Severity: critical" in result
    assert "Status: published" in result
    assert "Approval Level: director" in result

    # Test with unique_id
    result = sop_tool._prompt_common(unique_id="test-sop-123")
    assert "SOP ID (immutable): test-sop-123" in result


def test_build_prompt_yaml(sop_tool):
    """Test build_prompt for YAML format."""
    result = sop_tool.build_prompt("yaml", unique_id="test-id")
    assert "Return VALID YAML ONLY (no markdown fences)" in result
    assert "sop_id: (echo above)" in result
    assert "Problem category: general" in result
    assert "standard operating procedure (SOP) documents" in result


def test_build_prompt_json(sop_tool):
    """Test build_prompt for JSON format."""
    result = sop_tool.build_prompt("json", unique_id="test-id")
    assert "Return VALID JSON ONLY (no markdown fences)" in result
    assert '"sop_id": "(echo above)"' in result
    assert "Problem category: general" in result


def test_build_prompt_text(sop_tool):
    """Test build_prompt for text format."""
    result = sop_tool.build_prompt("txt", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "SOP ID: (echo above)" in result
    assert "Problem category: general" in result


def test_build_prompt_text_alias(sop_tool):
    """Test build_prompt for 'text' format (should normalize to 'txt')."""
    result = sop_tool.build_prompt("text", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "SOP ID: (echo above)" in result


def test_yaml_skeleton():
    """Test _yaml_skeleton returns expected YAML template."""
    result = TechSupportSOPTool._yaml_skeleton()
    assert "Return VALID YAML ONLY" in result
    assert "sop_id: (echo above)" in result
    assert "problem_description:" in result
    assert "resolution_steps:" in result
    assert "verification_steps:" in result
    assert "escalation:" in result
    assert "version_history:" in result


def test_json_skeleton():
    """Test _json_skeleton returns expected JSON template."""
    result = TechSupportSOPTool._json_skeleton()
    assert "Return VALID JSON ONLY" in result
    assert '"sop_id": "(echo above)"' in result
    assert '"problem_description":' in result
    assert '"resolution_steps": [' in result
    assert '"verification_steps": [' in result
    assert '"escalation": {' in result
    assert '"version_history": [' in result


def test_text_skeleton():
    """Test _text_skeleton returns expected text template."""
    result = TechSupportSOPTool._text_skeleton()
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "SOP ID: (echo above)" in result
    assert "PROBLEM DESCRIPTION:" in result
    assert "RESOLUTION STEPS:" in result
    assert "VERIFICATION STEPS:" in result
    assert "ESCALATION:" in result
    assert "VERSION HISTORY:" in result


def test_post_process_json_valid():
    """Test post_process with valid JSON."""
    tool = TechSupportSOPTool()
    valid_json = '{"sop_id": "123", "status": "approved", "severity": "high"}'
    result = tool.post_process(valid_json, "json")
    assert isinstance(result, dict)
    assert result["sop_id"] == "123"
    assert result["status"] == "approved"
    assert result["severity"] == "high"


def test_post_process_json_invalid():
    """Test post_process with invalid JSON returns raw string."""
    tool = TechSupportSOPTool()
    invalid_json = '{"sop_id": "123", unclosed_bracket'
    result = tool.post_process(invalid_json, "json")
    assert result == invalid_json


def test_post_process_yaml_valid():
    """Test post_process with valid YAML."""
    tool = TechSupportSOPTool()
    valid_yaml = "sop_id: 123\nstatus: approved\nseverity: high"
    result = tool.post_process(valid_yaml, "yaml")
    assert isinstance(result, dict)
    assert result["sop_id"] == 123
    assert result["status"] == "approved"
    assert result["severity"] == "high"


def test_post_process_yaml_invalid():
    """Test post_process with invalid YAML returns raw string."""
    tool = TechSupportSOPTool()
    invalid_yaml = "sop_id: 123\ninvalid:\n  - missing colon\n  item"
    result = tool.post_process(invalid_yaml, "yaml")
    assert result == invalid_yaml


def test_post_process_text():
    """Test post_process with text format returns raw string."""
    tool = TechSupportSOPTool()
    text = "This is plain text SOP content"
    result = tool.post_process(text, "txt")
    assert result == text


def test_post_process_text_alias():
    """Test post_process with 'text' format alias returns raw string."""
    tool = TechSupportSOPTool()
    text = "This is plain text SOP content"
    result = tool.post_process(text, "text")
    assert result == text


def test_get_system_description_default(sop_tool):
    """Test get_system_description returns the correct value with defaults."""
    expected = "Tech support SOP for general problems in Generic enterprise IT environment"
    assert sop_tool.get_system_description() == expected


def test_get_system_description_custom(sop_tool_custom):
    """Test get_system_description returns the correct value with custom parameters."""
    expected = "Tech support SOP for network problems in Azure cloud environment"
    assert sop_tool_custom.get_system_description() == expected


def test_tool_name_and_registry():
    """Test that the tool has correct name and toolName attributes."""
    tool = TechSupportSOPTool()
    assert tool.name == "tech-support-sop"
    assert tool.toolName == "TechSupportSOP"


def test_problem_categories():
    """Test that all expected problem categories work correctly."""
    categories = ["general", "network", "application", "authentication", "hardware", "database", "cloud", "security"]
    for category in categories:
        tool = TechSupportSOPTool(problem_category=category)
        assert tool.problem_category == category


def test_complexity_levels():
    """Test that all complexity levels work correctly."""
    complexity_levels = ["simple", "medium", "complex"]
    for complexity in complexity_levels:
        tool = TechSupportSOPTool(complexity=complexity)
        assert tool.complexity == complexity


def test_build_prompt_includes_category_and_context():
    """Test that build_prompt includes category and context in the prompt."""
    tool = TechSupportSOPTool(
        problem_category="security",
        system_context="Cloud-native microservices architecture",
    )
    result = tool.build_prompt("yaml")
    assert "Problem category: security" in result
    assert "System context: Cloud-native microservices architecture" in result
