"""
Unit tests for the data_generator.tools.it_service_desk_ticket module.
"""

import argparse
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Import the module we want to test
from data_generator.tools.it_service_desk_ticket import ITServiceDeskTicketTool


@pytest.fixture
def it_ticket_tool():
    """Return a basic ITServiceDeskTicketTool instance for testing."""
    return ITServiceDeskTicketTool()


@pytest.fixture
def it_ticket_tool_custom():
    """Return an ITServiceDeskTicketTool instance with custom parameters."""
    return ITServiceDeskTicketTool(
        ticket_type="change",
        service="Email",
        sla_hours=48,
    )


def test_init_default():
    """Test initialization with default parameters."""
    tool = ITServiceDeskTicketTool()
    assert tool.ticket_type == "incident"
    assert tool.service == "General IT"
    assert tool.sla_hours == 72


def test_init_custom_parameters():
    """Test initialization with custom parameters."""
    tool = ITServiceDeskTicketTool(
        ticket_type="request",
        service="VPN",
        sla_hours=24,
    )
    assert tool.ticket_type == "request"
    assert tool.service == "VPN"
    assert tool.sla_hours == 24


def test_cli_arguments(it_ticket_tool):
    """Test cli_arguments returns the expected structure."""
    args = it_ticket_tool.cli_arguments()
    assert isinstance(args, list)
    assert len(args) == 3

    # Check ticket-type argument
    ticket_type_arg = next(arg for arg in args if "--ticket-type" in arg["flags"])
    assert ticket_type_arg["kwargs"]["choices"] == ["incident", "request", "change"]
    assert ticket_type_arg["kwargs"]["default"] == "incident"

    # Check service argument
    service_arg = next(arg for arg in args if "--service" in arg["flags"])
    assert service_arg["kwargs"]["default"] == "General IT"

    # Check sla-hours argument
    sla_arg = next(arg for arg in args if "--sla-hours" in arg["flags"])
    assert sla_arg["kwargs"]["type"] is int
    assert sla_arg["kwargs"]["default"] == 72


def test_validate_args_valid():
    """Test validate_args with valid arguments."""
    tool = ITServiceDeskTicketTool()
    ns = argparse.Namespace(
        ticket_type="change",
        service="Email Service",
        sla_hours=48,
    )
    tool.validate_args(ns)
    assert tool.ticket_type == "change"
    assert tool.service == "Email Service"
    assert tool.sla_hours == 48


def test_validate_args_clamp_sla_hours():
    """Test validate_args clamps sla_hours to valid range."""
    tool = ITServiceDeskTicketTool()

    # Test below minimum
    ns_low = argparse.Namespace(sla_hours=0)
    tool.validate_args(ns_low)
    assert tool.sla_hours == 1

    # Test above maximum
    ns_high = argparse.Namespace(sla_hours=1000)
    tool.validate_args(ns_high)
    assert tool.sla_hours == 720

    # Test valid range
    ns_valid = argparse.Namespace(sla_hours=100)
    tool.validate_args(ns_valid)
    assert tool.sla_hours == 100


def test_validate_args_defaults():
    """Test validate_args with missing arguments uses defaults."""
    tool = ITServiceDeskTicketTool()
    ns = argparse.Namespace()
    tool.validate_args(ns)
    assert tool.ticket_type == "incident"
    assert tool.service == "General IT"
    assert tool.sla_hours == 72


def test_examples(it_ticket_tool):
    """Test examples returns non-empty list of valid examples."""
    examples = it_ticket_tool.examples()
    assert isinstance(examples, list)
    assert len(examples) > 0
    assert all(isinstance(ex, str) for ex in examples)
    assert all("--scenario it-service-desk-ticket" in ex for ex in examples)


def test_supported_output_formats(it_ticket_tool):
    """Test supported_output_formats returns expected formats."""
    formats = it_ticket_tool.supported_output_formats()
    assert isinstance(formats, list)
    assert set(formats) == {"yaml", "json", "txt", "text"}


@patch("data_generator.tools.it_service_desk_ticket.random.choice")
def test_random_attributes(mock_choice, it_ticket_tool):
    """Test _random_attributes returns expected values."""
    # Configure mock to return fixed values
    mock_choice.side_effect = ["P2", "medium", "high", "assigned"]

    priority, impact, urgency, status = it_ticket_tool._random_attributes()

    assert priority == "P2"
    assert impact == "medium"
    assert urgency == "high"
    assert status == "assigned"
    assert mock_choice.call_count == 4


@patch("uuid.uuid4")
@patch("data_generator.tools.it_service_desk_ticket.datetime")
@patch("data_generator.tools.it_service_desk_ticket.ITServiceDeskTicketTool._random_attributes")
def test_prompt_common(mock_attrs, mock_datetime, mock_uuid, it_ticket_tool):
    """Test _prompt_common returns correctly formatted string."""
    # Configure mocks
    mock_attrs.return_value = ("P1", "high", "high", "new")
    mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
    mock_dt = MagicMock()
    mock_dt.now.return_value = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_dt.isoformat.return_value = "2023-01-01T12:00:00+00:00"
    mock_datetime.now.return_value = mock_dt

    # Test without unique_id
    result = it_ticket_tool._prompt_common()
    assert "Ticket ID (immutable): 12345678-1234-5678-1234-567812345678" in result
    assert "Ticket Type: incident" in result
    assert "Service: General IT" in result
    assert "Priority: P1" in result
    assert "Impact: high" in result
    assert "Urgency: high" in result
    assert "Status: new" in result
    assert "SLA Hours: 72" in result

    # Test with unique_id
    result = it_ticket_tool._prompt_common(unique_id="test-id-123")
    assert "Ticket ID (immutable): test-id-123" in result


def test_build_prompt_yaml(it_ticket_tool):
    """Test build_prompt for YAML format."""
    result = it_ticket_tool.build_prompt("yaml", unique_id="test-id")
    assert "Return VALID YAML ONLY (no markdown fences)" in result
    assert "ticket_id: (echo above)" in result
    assert "The service area being simulated" in result
    assert "IT service desk tickets for demonstrations" in result


def test_build_prompt_json(it_ticket_tool):
    """Test build_prompt for JSON format."""
    result = it_ticket_tool.build_prompt("json", unique_id="test-id")
    assert "Return VALID JSON ONLY (no markdown fences)" in result
    assert '"ticket_id": "(echo above)"' in result
    assert "The service area being simulated" in result


def test_build_prompt_text(it_ticket_tool):
    """Test build_prompt for text format."""
    result = it_ticket_tool.build_prompt("txt", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Ticket ID: (echo above)" in result
    assert "The service area being simulated" in result


def test_build_prompt_text_alias(it_ticket_tool):
    """Test build_prompt for 'text' format (should normalize to 'txt')."""
    result = it_ticket_tool.build_prompt("text", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Ticket ID: (echo above)" in result


def test_yaml_skeleton():
    """Test _yaml_skeleton returns expected YAML template."""
    result = ITServiceDeskTicketTool._yaml_skeleton()
    assert "Return VALID YAML ONLY" in result
    assert "ticket_id: (echo above)" in result
    assert "requester:" in result
    assert "work_notes:" in result
    assert "resolution:" in result


def test_json_skeleton():
    """Test _json_skeleton returns expected JSON template."""
    result = ITServiceDeskTicketTool._json_skeleton()
    assert "Return VALID JSON ONLY" in result
    assert '"ticket_id": "(echo above)"' in result
    assert '"requester": {' in result
    assert '"work_notes": [' in result
    assert '"resolution": {' in result


def test_text_skeleton():
    """Test _text_skeleton returns expected text template."""
    result = ITServiceDeskTicketTool._text_skeleton()
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Ticket ID: (echo above)" in result
    assert "Work Notes:" in result
    assert "Resolution:" in result


def test_post_process_json_valid():
    """Test post_process with valid JSON."""
    tool = ITServiceDeskTicketTool()
    valid_json = '{"ticket_id": "123", "status": "new"}'
    result = tool.post_process(valid_json, "json")
    assert isinstance(result, dict)
    assert result["ticket_id"] == "123"
    assert result["status"] == "new"


def test_post_process_json_invalid():
    """Test post_process with invalid JSON returns raw string."""
    tool = ITServiceDeskTicketTool()
    invalid_json = '{"ticket_id": "123", unclosed_bracket'
    result = tool.post_process(invalid_json, "json")
    assert result == invalid_json


def test_post_process_yaml_valid():
    """Test post_process with valid YAML."""
    tool = ITServiceDeskTicketTool()
    valid_yaml = "ticket_id: 123\nstatus: new"
    result = tool.post_process(valid_yaml, "yaml")
    assert isinstance(result, dict)
    assert result["ticket_id"] == 123
    assert result["status"] == "new"


def test_post_process_yaml_invalid():
    """Test post_process with invalid YAML returns raw string."""
    tool = ITServiceDeskTicketTool()
    invalid_yaml = "ticket_id: 123\ninvalid:\n  - missing colon\n  item"
    result = tool.post_process(invalid_yaml, "yaml")
    assert result == invalid_yaml


def test_post_process_text():
    """Test post_process with text format returns raw string."""
    tool = ITServiceDeskTicketTool()
    text = "This is plain text content"
    result = tool.post_process(text, "txt")
    assert result == text


def test_post_process_text_alias():
    """Test post_process with 'text' format alias returns raw string."""
    tool = ITServiceDeskTicketTool()
    text = "This is plain text content"
    result = tool.post_process(text, "text")
    assert result == text


def test_get_system_description_default(it_ticket_tool):
    """Test get_system_description returns the correct value with defaults."""
    assert it_ticket_tool.get_system_description() == "IT service desk tickets for General IT (incident)"


def test_get_system_description_custom(it_ticket_tool_custom):
    """Test get_system_description returns the correct value with custom parameters."""
    assert it_ticket_tool_custom.get_system_description() == "IT service desk tickets for Email (change)"


def test_tool_name_and_registry():
    """Test that the tool has correct name and toolName attributes."""
    tool = ITServiceDeskTicketTool()
    assert tool.name == "it-service-desk-ticket"
    assert tool.toolName == "ITServiceDeskTicket"
