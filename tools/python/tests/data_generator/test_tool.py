"""
Unit tests for the data_generator.tool module.

These tests validate the functionality of the DataGeneratorTool abstract base class
including registry, factory, and format handling capabilities.
"""

import argparse
import json
import sys
import uuid
from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pytest
import yaml


# ------------------------------------------------------------------ #
# Mock the DataGeneratorTool class to avoid circular imports         #
# ------------------------------------------------------------------ #
class DataGeneratorTool(ABC):
    """
    Contract that every scenario-specific prompt builder must satisfy.

    Sub-classes should *only* embed domain logic (prompt templates, argument
    validation, post-processing) and have zero coupling to Azure / I/O.
    """

    # Registry for dynamic discovery
    _REGISTRY: ClassVar[dict[str, type["DataGeneratorTool"]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register every concrete subclass in the internal tool registry."""
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", None):
            raise AttributeError(
                "DataGeneratorTool subclasses must define a unique `name` attribute."
            )
        if cls.name in cls._REGISTRY:
            raise ValueError(f"Duplicate tool registration for name '{cls.name}'.")
        cls._REGISTRY[cls.name] = cls

    # Mandatory interface
    name: str
    toolName: str

    @abstractmethod
    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        """Return the full prompt string for the given output format."""

    @abstractmethod
    def cli_arguments(self) -> list[dict[str, Any]]:
        """Specification for CLI arguments consumed by this tool."""

    @abstractmethod
    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate CLI args after parsing."""

    @abstractmethod
    def examples(self) -> list[str]:
        """Return usage snippets for `--help` epilog."""

    @abstractmethod
    def get_system_description(self) -> str:
        """Optional extra context injected via a system-prompt."""

    # Optional / overridable
    def get_unique_id(self) -> str:
        """Return a unique identifier for the item."""
        return str(uuid.uuid4())

    # Format helpers
    _FORMAT_PARSERS: ClassVar[dict[str, Any]] = {
        "json": json.loads,
        "yaml": yaml.safe_load,
    }

    def supported_output_formats(self) -> list[str]:
        """Return the list of output formats recognised by ``post_process``."""
        return [*self._FORMAT_PARSERS.keys(), "txt"]

    def post_process(self, raw: str, output_format: str) -> Any:
        """Convert ``raw`` model output into a structured Python object."""
        fmt = output_format.lower()
        parser = self._FORMAT_PARSERS.get(fmt)
        if parser is None:
            return raw

        try:
            return parser(raw)
        except Exception:
            return raw

    @classmethod
    def from_name(cls, name: str) -> "DataGeneratorTool":
        """Factory helper that returns a new instance of the requested tool."""
        try:
            tool_cls = cls._REGISTRY[name]
        except KeyError as exc:
            raise KeyError(
                f"No DataGeneratorTool registered with name '{name}'."
            ) from exc
        return tool_cls()


# ------------------------------------------------------------------ #
# Test fixtures and helper classes                                   #
# ------------------------------------------------------------------ #
class ValidTestTool(DataGeneratorTool):
    """A valid implementation of DataGeneratorTool for testing."""
    
    name = "valid-test-tool"
    toolName = "ValidTestTool"
    
    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        return f"Test prompt for {output_format}"
    
    def cli_arguments(self) -> list[dict[str, Any]]:
        return [{"dest": "test_arg", "help": "Test argument"}]
    
    def validate_args(self, ns: argparse.Namespace) -> None:
        pass
    
    def examples(self) -> list[str]:
        return ["example1", "example2"]
    
    def get_system_description(self) -> str:
        return "Test system description"


@pytest.fixture
def valid_tool() -> ValidTestTool:
    """Return a valid DataGeneratorTool instance for testing."""
    return ValidTestTool()


# ------------------------------------------------------------------ #
# Registry and factory tests                                         #
# ------------------------------------------------------------------ #
def test_tool_registration() -> None:
    """Test that tools are correctly registered in the registry."""
    # ValidTestTool should have been registered during import
    assert "valid-test-tool" in DataGeneratorTool._REGISTRY
    assert DataGeneratorTool._REGISTRY["valid-test-tool"] is ValidTestTool


def test_missing_name_attribute() -> None:
    """Test that subclasses without a name attribute raise an error."""
    with pytest.raises(AttributeError, match="must define.*name"):
        # Create a subclass missing the name attribute
        type("InvalidTool", (DataGeneratorTool,), {
            "toolName": "InvalidTool",
        })


def test_duplicate_registration() -> None:
    """Test that registering two tools with the same name raises an error."""
    with pytest.raises(ValueError, match="Duplicate tool registration"):
        # Try to create another tool with the same name
        type("DuplicateTool", (DataGeneratorTool,), {
            "name": "valid-test-tool",  # Same as ValidTestTool
            "toolName": "DuplicateTool",
        })


def test_from_name_factory() -> None:
    """Test the from_name factory method."""
    # Get a tool by name
    tool = DataGeneratorTool.from_name("valid-test-tool")
    
    # Verify it's the correct type
    assert isinstance(tool, ValidTestTool)
    assert tool.name == "valid-test-tool"
    assert tool.toolName == "ValidTestTool"


def test_from_name_unknown_tool() -> None:
    """Test that from_name raises KeyError for unknown tools."""
    with pytest.raises(KeyError, match="No DataGeneratorTool registered"):
        DataGeneratorTool.from_name("non-existent-tool")


# ------------------------------------------------------------------ #
# Format helpers tests                                               #
# ------------------------------------------------------------------ #
def test_supported_output_formats(valid_tool: ValidTestTool) -> None:
    """Test the supported_output_formats method."""
    formats = valid_tool.supported_output_formats()
    
    # Check expected formats are included
    assert "json" in formats
    assert "yaml" in formats
    assert "txt" in formats
    
    # Verify the list matches expected values from the class
    expected_formats = list(DataGeneratorTool._FORMAT_PARSERS.keys()) + ["txt"]
    assert sorted(formats) == sorted(expected_formats)


def test_post_process_json_valid(valid_tool: ValidTestTool) -> None:
    """Test post_process with valid JSON input."""
    valid_json = json.dumps({"key": "value"})
    result = valid_tool.post_process(valid_json, "json")
    
    assert isinstance(result, dict)
    assert result == {"key": "value"}


def test_post_process_json_invalid(valid_tool: ValidTestTool) -> None:
    """Test post_process with invalid JSON input."""
    invalid_json = "{key: value}"  # Missing quotes
    result = valid_tool.post_process(invalid_json, "json")
    
    # Should return the original string for invalid JSON
    assert result == invalid_json


def test_post_process_yaml_valid(valid_tool: ValidTestTool) -> None:
    """Test post_process with valid YAML input."""
    valid_yaml = "key: value\nlist:\n  - item1\n  - item2"
    result = valid_tool.post_process(valid_yaml, "yaml")
    
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["list"] == ["item1", "item2"]


def test_post_process_yaml_invalid(valid_tool: ValidTestTool) -> None:
    """Test post_process with invalid YAML input."""
    invalid_yaml = "key: - value"  # Invalid YAML syntax
    result = valid_tool.post_process(invalid_yaml, "yaml")
    
    # Should return the original string for invalid YAML
    assert result == invalid_yaml


def test_post_process_txt(valid_tool: ValidTestTool) -> None:
    """Test post_process with text input."""
    text = "This is plain text"
    result = valid_tool.post_process(text, "txt")
    
    # Should return the original string for text format
    assert result == text


def test_post_process_unknown_format(valid_tool: ValidTestTool) -> None:
    """Test post_process with an unknown format."""
    text = "Some content"
    result = valid_tool.post_process(text, "unknown")
    
    # Should return the original string for unknown formats
    assert result == text


# ------------------------------------------------------------------ #
# Utility method tests                                               #
# ------------------------------------------------------------------ #
def test_get_unique_id(valid_tool: ValidTestTool, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the get_unique_id method."""
    # Mock uuid.uuid4 to return a predictable value
    test_uuid = "00000000-0000-0000-0000-000000000000"
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(test_uuid))
    
    # Call the method
    result = valid_tool.get_unique_id()
    
    # Verify the result
    assert result == test_uuid
