"""
Unit tests for the data_generator.tools.travel_booking module.
"""

import argparse
from datetime import timezone
from unittest.mock import MagicMock, patch

import pytest

# Import the module we want to test
from data_generator.tools.travel_booking import TravelBookingTool


@pytest.fixture
def travel_booking_tool():
    """Return a basic TravelBookingTool instance for testing."""
    return TravelBookingTool()


@pytest.fixture
def travel_booking_with_params():
    """Return a TravelBookingTool instance with custom parameters."""
    return TravelBookingTool(trip_type="flight", region="Europe")


def test_init_default():
    """Test initialization with default parameters."""
    tool = TravelBookingTool()
    assert tool.trip_type == "flight+hotel"
    assert tool.region == "global"


def test_init_custom_params():
    """Test initialization with custom parameters."""
    tool = TravelBookingTool(trip_type="hotel", region="Asia")
    assert tool.trip_type == "hotel"
    assert tool.region == "Asia"


def test_name_and_tool_name():
    """Test class-level name and toolName attributes."""
    assert TravelBookingTool.name == "travel-booking"
    assert TravelBookingTool.toolName == "TravelBooking"


def test_cli_arguments(travel_booking_tool):
    """Test cli_arguments returns the expected structure."""
    args = travel_booking_tool.cli_arguments()
    assert isinstance(args, list)
    assert len(args) == 2

    # Check trip-type argument
    trip_type_arg = args[0]
    assert "flags" in trip_type_arg
    assert "--trip-type" in trip_type_arg["flags"]
    assert "kwargs" in trip_type_arg
    assert trip_type_arg["kwargs"]["choices"] == ["flight", "hotel", "flight+hotel"]
    assert trip_type_arg["kwargs"]["default"] == "flight+hotel"

    # Check region argument
    region_arg = args[1]
    assert "flags" in region_arg
    assert "--region" in region_arg["flags"]
    assert "kwargs" in region_arg
    assert region_arg["kwargs"]["default"] == "global"


def test_validate_args_valid():
    """Test validate_args with valid arguments."""
    tool = TravelBookingTool()
    ns = argparse.Namespace(trip_type="flight", region="Europe")
    tool.validate_args(ns)
    assert tool.trip_type == "flight"
    assert tool.region == "Europe"


def test_validate_args_invalid_trip_type():
    """Test validate_args normalizes invalid trip_type to default."""
    tool = TravelBookingTool()
    ns = argparse.Namespace(trip_type="invalid", region="Asia")
    tool.validate_args(ns)
    assert tool.trip_type == "flight+hotel"  # should default
    assert tool.region == "Asia"


def test_validate_args_missing():
    """Test validate_args with missing arguments uses defaults."""
    tool = TravelBookingTool()
    ns = argparse.Namespace()
    tool.validate_args(ns)
    assert tool.trip_type == "flight+hotel"
    assert tool.region == "global"


def test_examples(travel_booking_tool):
    """Test examples returns a list of usage strings."""
    examples = travel_booking_tool.examples()
    assert isinstance(examples, list)
    assert len(examples) == 1
    assert "travel-booking" in examples[0]
    assert "--trip-type flight+hotel" in examples[0]
    assert "--region Europe" in examples[0]


def test_supported_output_formats(travel_booking_tool):
    """Test supported_output_formats returns expected formats."""
    formats = travel_booking_tool.supported_output_formats()
    assert formats == ["yaml", "json", "text"]


def test_build_prompt_yaml(travel_booking_tool):
    """Test build_prompt for YAML format."""
    result = travel_booking_tool.build_prompt("yaml", unique_id="test-id")
    assert "Return VALID YAML ONLY (no markdown fences)" in result
    assert "booking_id: (echo above)" in result
    assert "traveler:" in result
    assert "itinerary:" in result
    assert "test-id" in result  # unique_id should be in prompt


def test_build_prompt_json(travel_booking_tool):
    """Test build_prompt for JSON format."""
    result = travel_booking_tool.build_prompt("json", unique_id="test-id")
    assert "Return VALID JSON ONLY (no markdown fences)" in result
    assert '"booking_id": "(echo above)"' in result
    assert '"traveler"' in result
    assert '"itinerary"' in result
    assert "test-id" in result


def test_build_prompt_text(travel_booking_tool):
    """Test build_prompt for text format."""
    result = travel_booking_tool.build_prompt("text", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Booking ID: (echo above)" in result
    assert "TRAVELER INFORMATION:" in result
    assert "test-id" in result


def test_build_prompt_txt_format(travel_booking_tool):
    """Test build_prompt also handles 'txt' format (alias for text)."""
    result = travel_booking_tool.build_prompt("txt", unique_id="test-id")
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Booking ID: (echo above)" in result


def test_yaml_skeleton():
    """Test _yaml_skeleton returns expected YAML template."""
    result = TravelBookingTool._yaml_skeleton()
    assert "Return VALID YAML ONLY" in result
    assert "booking_id: (echo above)" in result
    assert "traveler:" in result
    assert "itinerary:" in result
    assert "flights:" in result
    assert "hotels:" in result
    assert "total_cost:" in result


def test_json_skeleton():
    """Test _json_skeleton returns expected JSON template."""
    result = TravelBookingTool._json_skeleton()
    assert "Return VALID JSON ONLY" in result
    assert '"booking_id": "(echo above)"' in result
    assert '"traveler"' in result
    assert '"itinerary"' in result
    assert '"flights"' in result
    assert '"hotels"' in result


def test_text_skeleton():
    """Test _text_skeleton returns expected text template."""
    result = TravelBookingTool._text_skeleton()
    assert "Return plain text WITHOUT any YAML/JSON formatting markers" in result
    assert "Booking ID: (echo above)" in result
    assert "TRAVELER INFORMATION:" in result
    assert "FLIGHT DETAILS:" in result
    assert "HOTEL DETAILS:" in result


def test_post_process_json_valid():
    """Test post_process with valid JSON."""
    tool = TravelBookingTool()
    valid_json = '{"booking_id": "123", "trip_type": "flight+hotel"}'
    result = tool.post_process(valid_json, "json")
    assert isinstance(result, dict)
    assert result["booking_id"] == "123"
    assert result["trip_type"] == "flight+hotel"


def test_post_process_json_invalid():
    """Test post_process with invalid JSON returns raw string."""
    tool = TravelBookingTool()
    invalid_json = '{"booking_id": "123", unclosed_bracket'
    result = tool.post_process(invalid_json, "json")
    assert result == invalid_json


def test_post_process_yaml_valid():
    """Test post_process with valid YAML."""
    tool = TravelBookingTool()
    valid_yaml = "booking_id: test\ntrip_type: flight\nregion: global"
    result = tool.post_process(valid_yaml, "yaml")
    assert isinstance(result, dict)
    assert result["booking_id"] == "test"
    assert result["trip_type"] == "flight"


def test_post_process_yaml_invalid():
    """Test post_process with invalid YAML returns raw string."""
    tool = TravelBookingTool()
    invalid_yaml = "booking_id: test\ninvalid:\n  - missing colon\n  item"
    result = tool.post_process(invalid_yaml, "yaml")
    assert result == invalid_yaml


def test_post_process_text():
    """Test post_process with text format returns raw string."""
    tool = TravelBookingTool()
    text = "This is plain text booking content"
    result = tool.post_process(text, "text")
    assert result == text


def test_post_process_txt():
    """Test post_process with txt format returns raw string."""
    tool = TravelBookingTool()
    text = "This is plain text booking content"
    result = tool.post_process(text, "txt")
    assert result == text


def test_get_system_description_default():
    """Test get_system_description with default values."""
    tool = TravelBookingTool()
    desc = tool.get_system_description()
    assert desc == "Travel bookings (flight+hotel) in global"


def test_get_system_description_custom():
    """Test get_system_description with custom values."""
    tool = TravelBookingTool(trip_type="hotel", region="Europe")
    desc = tool.get_system_description()
    assert desc == "Travel bookings (hotel) in Europe"


def test_random_attributes():
    """Test _random_attributes returns valid values."""
    tool = TravelBookingTool()
    status, airline, hotel = tool._random_attributes()

    assert status in tool._BOOKING_STATUS
    assert airline in tool._AIRLINES
    assert hotel in tool._HOTEL_CHAINS


def test_prompt_common_content():
    """Test _prompt_common includes required elements."""
    tool = TravelBookingTool(trip_type="flight", region="Asia")
    result = tool._prompt_common(unique_id="test-123")

    assert "test-123" in result
    assert "flight" in result
    assert "Asia" in result
    assert "ISO-8601" in result


def test_prompt_common_generates_uuid_if_no_unique_id():
    """Test _prompt_common generates UUID when unique_id is None."""
    tool = TravelBookingTool()
    result = tool._prompt_common()

    # Should contain a UUID-like string
    assert len([line for line in result.split('\n') if 'Booking ID' in line]) == 1


@patch('data_generator.tools.travel_booking.datetime')
def test_prompt_common_uses_current_time(mock_datetime):
    """Test _prompt_common uses current UTC time."""
    mock_now = MagicMock()
    mock_now.isoformat.return_value = "2023-01-01T12:00:00+00:00"
    mock_datetime.now.return_value = mock_now
    mock_datetime.timezone = timezone

    tool = TravelBookingTool()
    result = tool._prompt_common()

    mock_datetime.now.assert_called_once_with(timezone.utc)
    assert "2023-01-01T12:00:00+00:00" in result


def test_build_prompt_includes_trip_type_and_region():
    """Test build_prompt includes the tool's trip_type and region."""
    tool = TravelBookingTool(trip_type="hotel", region="Europe")
    result = tool.build_prompt("yaml")

    assert "hotel" in result
    assert "Europe" in result


def test_tool_registration():
    """Test that the tool is properly registered with DataGeneratorTool."""
    # The tool should be registered automatically via __init_subclass__
    from data_generator.tool import DataGeneratorTool

    assert "travel-booking" in DataGeneratorTool._REGISTRY
    assert DataGeneratorTool._REGISTRY["travel-booking"] == TravelBookingTool
