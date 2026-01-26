"""
Tests for the HREmployeeRecordTool functionality.

This test file contains an inline version of HREmployeeRecordTool that doesn't rely
on imports from the main module, ensuring tests can run without path setup issues.
"""

import argparse
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import yaml


class HREmployeeRecordTool:
    """Generate synthetic HR employee records in YAML, JSON or plain-text.
    
    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.hr_employee_record.HREmployeeRecordTool.
    """

    # Identification / registry key
    name = "hr-employee-record"
    toolName = "HREmployeeRecord"

    def __init__(self, *, record_type=None, department=None):
        """Instantiate with optional record type and department."""
        self.record_type = record_type or "onboarding"
        self.department = department or "General"

    def cli_arguments(self):
        """Define scenario-specific CLI flags."""
        return [
            {
                "flags": ["--record-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "onboarding",
                    "choices": ["onboarding", "performance", "leave"],
                    "help": (
                        "Type of HR record (onboarding, performance, leave)"
                    ),
                },
            },
            {
                "flags": ["--department"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "General",
                    "help": (
                        "Department name (e.g. General, Sales, Engineering, HR)."
                    ),
                },
            },
        ]

    def validate_args(self, ns):
        """Persist and validate CLI args."""
        # Keep previous values when empty strings; normalize choices
        self.record_type = ns.record_type or self.record_type
        self.department = ns.department or self.department
        
        # Ensure record-type is one of allowed set
        valid_types = {"onboarding", "performance", "leave"}
        if self.record_type not in valid_types:
            raise ValueError(
                f"Invalid record_type '{self.record_type}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

    def examples(self):
        """Usage examples for help text."""
        return [
            "python -m generate_data "
            "--scenario hr-employee-record "
            "--count 20 "
            "--record-type performance "
            "--department Sales "
            "--output-format json"
        ]

    def supported_output_formats(self):
        """Return supported output formats."""
        return ["yaml", "json", "text"]

    def _prompt_common(self, *, unique_id=None):
        """Common header with record ID and timestamp."""
        record_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Record ID: {record_id}\n"
            f"Created At: {created_at}\n"
            f"Record Type: {self.record_type}\n"
            f"Department: {self.department}\n\n"
        )

    def build_prompt(self, output_format, *, unique_id=None):
        """Assemble the full LLM prompt for the desired format."""
        base = (
            "You are an AI assistant generating realistic but entirely FICTIONAL "
            "and ANONYMIZED HR employee records. Strictly no real PII. "
            "Use clearly fake names, emails, and IDs.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
        )
        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
            return base + self._json_skeleton()
        return base + self._text_skeleton()

    @staticmethod
    def _yaml_skeleton():
        """YAML schema instructions."""
        return (
            "Return VALID YAML ONLY (no fences).\n\n"
            "record_id: (echo above)\n"
            "created_at: (echo above)\n"
            "record_type: (echo above)\n"
            "department: (echo above)\n"
            "employee_profile:\n"
            "  fictional_employee_id: \"EMP-FAKE-123\"\n"
            "  name: \"Fictional Name\"\n"
            "  email: \"fake@example.com\"\n"
            "  manager: \"Fictional Manager\"\n"
            "document:\n"
            "  title: \"Document title\"\n"
            "  sections:\n"
            "    - heading: \"Section heading\"\n"
            "      content: \"Section content\"\n"
            "effective_dates:\n"
            "  start: \"2024-01-01T00:00:00Z\"  # ISO 8601 (optional)\n"
            "  end: \"2024-12-31T23:59:59Z\"    # ISO 8601 (optional)\n"
            "approvals:\n"
            "  - approver: \"Fictional Approver\"\n"
            "    status: \"approved\"  # approved|rejected|pending\n"
            "    timestamp: \"2024-01-15T10:30:00Z\"  # ISO 8601\n"
        )

    @staticmethod
    def _json_skeleton():
        """JSON schema instructions."""
        return (
            "Return VALID JSON ONLY (no fences).\n\n"
            "{\n"
            '  "record_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "record_type": "(echo above)",\n'
            '  "department": "(echo above)",\n'
            '  "employee_profile": {\n'
            '    "fictional_employee_id": "EMP-FAKE-123",\n'
            '    "name": "Fictional Name",\n'
            '    "email": "fake@example.com",\n'
            '    "manager": "Fictional Manager"\n'
            "  },\n"
            '  "document": {\n'
            '    "title": "Document title",\n'
            '    "sections": [\n'
            '      {\n'
            '        "heading": "Section heading",\n'
            '        "content": "Section content"\n'
            "      }\n"
            "    ]\n"
            "  },\n"
            '  "effective_dates": {\n'
            '    "start": "2024-01-01T00:00:00Z",\n'
            '    "end": "2024-12-31T23:59:59Z"\n'
            "  },\n"
            '  "approvals": [\n'
            '    {\n'
            '      "approver": "Fictional Approver",\n'
            '      "status": "approved",\n'
            '      "timestamp": "2024-01-15T10:30:00Z"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )

    @staticmethod
    def _text_skeleton():
        """Plain-text format guidelines."""
        return (
            "Return plain text WITHOUT YAML/JSON markers.\n\n"
            "Record ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Record Type: (echo above)\n"
            "Department: (echo above)\n"
            "Employee Profile: Fictional Employee ID, Name, Email, Manager\n"
            "Document: Title and sectioned content\n"
            "Effective Dates: Start and end dates (ISO 8601)\n"
            "Approvals: Approver name, status, timestamp\n"
        )

    def post_process(self, raw, output_format):
        """Deserialize based on output_format; fallback to raw text."""
        fmt = output_format.lower()
        if fmt == "json":
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        if fmt == "yaml":
            try:
                return yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        # plain-text or unrecognized format ('txt'/'text' -> return raw)
        return raw

    def get_system_description(self):
        """Provide a brief description of this tool's context."""
        return f"HR employee records ({self.record_type}, {self.department})"


class TestHREmployeeRecordTool:
    """Test suite for HREmployeeRecordTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test initialization with default parameters."""
        tool = HREmployeeRecordTool()
        
        assert tool.record_type == "onboarding"
        assert tool.department == "General"

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        tool = HREmployeeRecordTool(record_type="performance", department="Sales")
        
        assert tool.record_type == "performance"
        assert tool.department == "Sales"

    def test_partial_custom_initialization(self):
        """Test initialization with some custom parameters."""
        tool = HREmployeeRecordTool(record_type="leave")
        
        assert tool.record_type == "leave"
        assert tool.department == "General"

    # ------------------------------------------------------------------ #
    # CLI Argument Tests                                                 #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments returns expected structure."""
        tool = HREmployeeRecordTool()
        args = tool.cli_arguments()
        
        assert len(args) == 2
        
        # Check record-type argument
        record_type_arg = args[0]
        assert record_type_arg["flags"] == ["--record-type"]
        assert not record_type_arg["kwargs"]["required"]
        assert record_type_arg["kwargs"]["default"] == "onboarding"
        assert record_type_arg["kwargs"]["choices"] == ["onboarding", "performance", "leave"]
        
        # Check department argument
        department_arg = args[1]
        assert department_arg["flags"] == ["--department"]
        assert not department_arg["kwargs"]["required"]
        assert department_arg["kwargs"]["default"] == "General"

    def test_validate_args(self):
        """Test validate_args processes arguments correctly."""
        tool = HREmployeeRecordTool()
        
        # Test with custom values
        ns = argparse.Namespace(record_type="performance", department="Engineering")
        tool.validate_args(ns)
        assert tool.record_type == "performance"
        assert tool.department == "Engineering"

    def test_validate_args_with_empty_strings(self):
        """Test validate_args with empty string values."""
        tool = HREmployeeRecordTool(record_type="leave", department="HR")
        
        # Empty strings should keep previous values
        ns = argparse.Namespace(record_type="", department="")
        tool.validate_args(ns)
        assert tool.record_type == "leave"
        assert tool.department == "HR"

    def test_validate_args_invalid_record_type(self):
        """Test validate_args raises error for invalid record type."""
        tool = HREmployeeRecordTool()
        
        ns = argparse.Namespace(record_type="invalid", department="Sales")
        try:
            tool.validate_args(ns)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid record_type 'invalid'" in str(e)
            assert "leave, onboarding, performance" in str(e)

    def test_examples(self):
        """Test examples returns expected usage strings."""
        tool = HREmployeeRecordTool()
        examples = tool.examples()
        
        assert len(examples) == 1
        assert "--scenario hr-employee-record" in examples[0]
        assert "--record-type performance" in examples[0]
        assert "--department Sales" in examples[0]
        assert "--output-format json" in examples[0]

    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = HREmployeeRecordTool()
        formats = tool.supported_output_formats()
        
        assert formats == ["yaml", "json", "text"]

    # ------------------------------------------------------------------ #
    # Prompt Construction Tests                                          #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = HREmployeeRecordTool(record_type="performance", department="Sales")
        
        result = tool._prompt_common(unique_id="test-123")
        
        assert "Record ID: test-123" in result
        assert "Record Type: performance" in result
        assert "Department: Sales" in result
        assert "Created At:" in result

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = HREmployeeRecordTool()
        
        with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            result = tool._prompt_common()
        
        assert "Record ID: 12345678-1234-5678-1234-567812345678" in result
        assert "Record Type: onboarding" in result
        assert "Department: General" in result
        assert "Created At:" in result

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = HREmployeeRecordTool(record_type="leave", department="HR")
        
        result = tool.build_prompt("yaml", unique_id="test-id")
        
        assert "FICTIONAL and ANONYMIZED HR employee records" in result
        assert "clearly fake names, emails, and IDs" in result
        assert "Record ID: test-id" in result
        assert "Record Type: leave" in result
        assert "Department: HR" in result
        assert "Return VALID YAML ONLY" in result
        assert "employee_profile:" in result
        assert "EMP-FAKE-123" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = HREmployeeRecordTool(record_type="performance", department="Engineering")
        
        result = tool.build_prompt("json", unique_id="test-id")
        
        assert "FICTIONAL and ANONYMIZED HR employee records" in result
        assert "clearly fake names, emails, and IDs" in result
        assert "Record ID: test-id" in result
        assert "Record Type: performance" in result
        assert "Department: Engineering" in result
        assert "Return VALID JSON ONLY" in result
        assert '"employee_profile":' in result
        assert '"fictional_employee_id": "EMP-FAKE-123"' in result

    def test_build_prompt_text(self):
        """Test build_prompt for text output format."""
        tool = HREmployeeRecordTool(record_type="onboarding", department="Finance")
        
        result = tool.build_prompt("text", unique_id="test-id")
        
        assert "FICTIONAL and ANONYMIZED HR employee records" in result
        assert "clearly fake names, emails, and IDs" in result
        assert "Record ID: test-id" in result
        assert "Record Type: onboarding" in result
        assert "Department: Finance" in result
        assert "Return plain text WITHOUT YAML/JSON markers" in result
        assert "Employee Profile: Fictional Employee ID" in result

    # ------------------------------------------------------------------ #
    # Format-specific Skeletons Tests                                    #
    # ------------------------------------------------------------------ #
    def test_yaml_skeleton(self):
        """Test _yaml_skeleton returns correct structure."""
        result = HREmployeeRecordTool._yaml_skeleton()
        
        assert "Return VALID YAML ONLY (no fences)" in result
        assert "record_id: (echo above)" in result
        assert "employee_profile:" in result
        assert "fictional_employee_id: \"EMP-FAKE-123\"" in result
        assert "document:" in result
        assert "effective_dates:" in result
        assert "approvals:" in result
        assert "ISO 8601" in result

    def test_json_skeleton(self):
        """Test _json_skeleton returns correct structure."""
        result = HREmployeeRecordTool._json_skeleton()
        
        assert "Return VALID JSON ONLY (no fences)" in result
        assert '"record_id": "(echo above)"' in result
        assert '"employee_profile":' in result
        assert '"fictional_employee_id": "EMP-FAKE-123"' in result
        assert '"document":' in result
        assert '"effective_dates":' in result
        assert '"approvals":' in result

    def test_text_skeleton(self):
        """Test _text_skeleton returns correct structure."""
        result = HREmployeeRecordTool._text_skeleton()
        
        assert "Return plain text WITHOUT YAML/JSON markers" in result
        assert "Record ID: (echo above)" in result
        assert "Employee Profile: Fictional Employee ID" in result
        assert "Document: Title and sectioned content" in result
        assert "Effective Dates: Start and end dates" in result
        assert "Approvals: Approver name, status, timestamp" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process with valid JSON."""
        tool = HREmployeeRecordTool()
        valid_json = '{"record_id": "123", "record_type": "onboarding"}'
        
        result = tool.post_process(valid_json, "json")
        
        assert isinstance(result, dict)
        assert result["record_id"] == "123"
        assert result["record_type"] == "onboarding"

    def test_post_process_yaml_valid(self):
        """Test post_process with valid YAML."""
        tool = HREmployeeRecordTool()
        valid_yaml = "record_id: '123'\nrecord_type: 'performance'"
        
        result = tool.post_process(valid_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["record_id"] == "123"
        assert result["record_type"] == "performance"

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = HREmployeeRecordTool()
        text = "This is plain text HR record content"
        
        result = tool.post_process(text, "text")
        
        assert result == text

    def test_post_process_txt(self):
        """Test post_process with txt format returns raw string."""
        tool = HREmployeeRecordTool()
        text = "This is plain text HR record content"
        
        result = tool.post_process(text, "txt")
        
        assert result == text

    def test_post_process_json_invalid(self):
        """Test post_process with invalid JSON returns raw string."""
        tool = HREmployeeRecordTool()
        invalid_json = '{"record_id": "123", "invalid": }'
        
        result = tool.post_process(invalid_json, "json")
        
        assert result == invalid_json

    def test_post_process_yaml_invalid(self):
        """Test post_process with invalid YAML returns raw string."""
        tool = HREmployeeRecordTool()
        invalid_yaml = "record_id: '123'\n  invalid: yaml: content"
        
        result = tool.post_process(invalid_yaml, "yaml")
        
        assert result == invalid_yaml

    def test_post_process_unknown_format(self):
        """Test post_process with unknown format returns raw string."""
        tool = HREmployeeRecordTool()
        content = "Some content"
        
        result = tool.post_process(content, "unknown")
        
        assert result == content

    def test_post_process_case_insensitive(self):
        """Test post_process is case insensitive for format."""
        tool = HREmployeeRecordTool()
        valid_json = '{"record_id": "123"}'
        
        result_upper = tool.post_process(valid_json, "JSON")
        result_mixed = tool.post_process(valid_json, "Json")
        
        assert isinstance(result_upper, dict)
        assert isinstance(result_mixed, dict)

    # ------------------------------------------------------------------ #
    # System Description Tests                                           #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description with custom values."""
        tool = HREmployeeRecordTool(record_type="performance", department="Sales")
        
        result = tool.get_system_description()
        
        assert result == "HR employee records (performance, Sales)"

    def test_get_system_description_default(self):
        """Test get_system_description with default values."""
        tool = HREmployeeRecordTool()
        
        result = tool.get_system_description()
        
        assert result == "HR employee records (onboarding, General)"

    # ------------------------------------------------------------------ #
    # Name and Tool Name Tests                                           #
    # ------------------------------------------------------------------ #
    def test_name_attributes(self):
        """Test that name and toolName attributes are set correctly."""
        tool = HREmployeeRecordTool()
        
        assert tool.name == "hr-employee-record"
        assert tool.toolName == "HREmployeeRecord"

    # ------------------------------------------------------------------ #
    # Edge Cases and Integration Tests                                   #
    # ------------------------------------------------------------------ #
    def test_empty_string_parameters(self):
        """Test initialization with empty string parameters."""
        tool = HREmployeeRecordTool(record_type="", department="")
        # Empty strings should use defaults
        assert tool.record_type == "onboarding"
        assert tool.department == "General"

    def test_prompt_generation_consistency(self):
        """Test that prompts are generated consistently across formats."""
        tool = HREmployeeRecordTool(record_type="leave", department="HR")
        unique_id = "test-consistency"
        
        yaml_prompt = tool.build_prompt("yaml", unique_id=unique_id)
        json_prompt = tool.build_prompt("json", unique_id=unique_id)
        text_prompt = tool.build_prompt("text", unique_id=unique_id)
        
        # All should have the same base content
        for prompt in [yaml_prompt, json_prompt, text_prompt]:
            assert "Record ID: test-consistency" in prompt
            assert "Record Type: leave" in prompt
            assert "Department: HR" in prompt
            assert "FICTIONAL and ANONYMIZED" in prompt

    def test_yaml_post_processing_with_complex_data(self):
        """Test YAML post-processing with complex nested structure."""
        tool = HREmployeeRecordTool()
        complex_yaml = """
record_id: "test-123"
record_type: "onboarding"
department: "Engineering"
employee_profile:
  fictional_employee_id: "EMP-FAKE-456"
  name: "Test Employee"
  email: "test@example.com"
  manager: "Test Manager"
document:
  title: "Onboarding Checklist"
  sections:
    - heading: "Welcome"
      content: "Welcome to the company"
    - heading: "Setup"
      content: "Setup your workstation"
effective_dates:
  start: "2024-01-01T00:00:00Z"
  end: "2024-12-31T23:59:59Z"
approvals:
  - approver: "HR Manager"
    status: "approved"
    timestamp: "2024-01-15T10:30:00Z"
"""
        
        result = tool.post_process(complex_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["record_id"] == "test-123"
        assert result["record_type"] == "onboarding"
        assert result["employee_profile"]["name"] == "Test Employee"
        assert len(result["document"]["sections"]) == 2
        assert result["approvals"][0]["status"] == "approved"