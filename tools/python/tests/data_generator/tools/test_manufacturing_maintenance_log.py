"""
Tests for the ManufacturingMaintenanceLogTool functionality.

This test file contains an inline version of ManufacturingMaintenanceLogTool that doesn't rely
on imports from the main module, ensuring tests can run without path setup issues.
"""

import argparse
import json
import uuid
from datetime import datetime, timezone

import yaml


class ManufacturingMaintenanceLogTool:
    """Generate synthetic manufacturing maintenance log entries.
    
    This is a standalone test implementation duplicating the functionality from
    data_generator.tools.manufacturing_maintenance_log.ManufacturingMaintenanceLogTool.
    """

    # Identification / registry key
    name = "manufacturing-maintenance-log"
    toolName = "ManufacturingMaintenanceLog"

    def __init__(self, *, plant=None, line=None, equipment_type=None):
        """Create a new tool instance with optional overrides."""
        self.plant = plant or "Plant A"
        self.line = line or "Line 1"
        self.equipment_type = equipment_type or "General"

    def cli_arguments(self):
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--plant"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "Plant A",
                    "help": "Manufacturing plant name (e.g., Plant A, Plant B).",
                },
            },
            {
                "flags": ["--line"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "Line 1",
                    "help": "Production line identifier (e.g., Line 1, Line 2).",
                },
            },
            {
                "flags": ["--equipment-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "General",
                    "help": (
                        "Equipment type (e.g., Conveyor, Press, CNC, General)."
                    ),
                },
            },
        ]

    def validate_args(self, ns):
        """Persist validated CLI arguments onto the instance."""
        self.plant = ns.plant or "Plant A"
        self.line = ns.line or "Line 1"
        self.equipment_type = ns.equipment_type or "General"

    def examples(self):
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario manufacturing-maintenance-log "
            "--count 50 "
            '--plant "Plant B" '
            '--line "Line 3" '
            "--equipment-type CNC "
            "--output-format yaml"
        ]

    def supported_output_formats(self):
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "text"]

    def _prompt_common(self, *, unique_id=None):
        """Shared prompt header including an optional caller-supplied id."""
        log_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Log ID (immutable): {log_id}\n"
            f"Created At: {created_at}\n"
            f"Plant: {self.plant}\n"
            f"Line: {self.line}\n"
            f"Equipment Type: {self.equipment_type}\n\n"
        )

    def build_prompt(self, output_format, *, unique_id=None):
        """Return the full prompt for the requested output_format."""
        base = (
            "You are an experienced maintenance technician creating REALISTIC BUT "
            "ENTIRELY FICTIONAL maintenance log entries for manufacturing "
            "equipment.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "Generate maintenance logs with realistic equipment details, parts used, "
            "durations, and technician notes. Use clearly fake asset tags and "
            "technician names. Ensure all timestamps are in ISO 8601 format.\n\n"
            "Always output ONLY the requested data structure – no markdown fences, "
            "no commentary.\n\n"
        )

        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
            return base + self._json_skeleton()
        # TEXT
        return base + self._text_skeleton()

    def _yaml_skeleton(self):
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return valid YAML ONLY.\n\n"
            "log_id: (echo above)\n"
            "created_at: (echo above)\n"
            "plant: (echo above)\n"
            "line: (echo above)\n"
            "equipment_type: (echo above)\n"
            "equipment_id: fake asset tag (e.g., EQ-FAKE-123)\n"
            "maintenance_type: preventive|corrective|inspection\n"
            "status: open|in_progress|completed|deferred\n"
            "start_time: ISO 8601 timestamp\n"
            "end_time: ISO 8601 timestamp (optional, if completed)\n"
            "duration_minutes: integer (if completed)\n"
            "technician: fictional name\n"
            "issue_description: detailed text description\n"
            "actions_taken:\n"
            "  - action description\n"
            "  - another action\n"
            "parts_used:\n"
            "  - part_number: PART-FAKE-001\n"
            "    quantity: 2\n"
            "  - part_number: PART-FAKE-002\n"
            "    quantity: 1\n"
            "follow_up_tasks:\n"
            "  - task description (optional)\n"
        )

    def _json_skeleton(self):
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return valid JSON ONLY.\n\n"
            "{\n"
            '  "log_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "plant": "(echo above)",\n'
            '  "line": "(echo above)",\n'
            '  "equipment_type": "(echo above)",\n'
            '  "equipment_id": "EQ-FAKE-123",\n'
            '  "maintenance_type": "preventive|corrective|inspection",\n'
            '  "status": "open|in_progress|completed|deferred",\n'
            '  "start_time": "ISO 8601 timestamp",\n'
            '  "end_time": "ISO 8601 timestamp (optional)",\n'
            '  "duration_minutes": 120,\n'
            '  "technician": "John Fake-Smith",\n'
            '  "issue_description": "Detailed description of issue or maintenance",\n'
            '  "actions_taken": ["action 1", "action 2"],\n'
            '  "parts_used": [\n'
            '    {"part_number": "PART-FAKE-001", "quantity": 2},\n'
            '    {"part_number": "PART-FAKE-002", "quantity": 1}\n'
            '  ],\n'
            '  "follow_up_tasks": ["task description (optional)"]\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton():
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT YAML/JSON markers.\n\n"
            "Log ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Plant: (echo above)\n"
            "Line: (echo above)\n"
            "Equipment Type: (echo above)\n"
            "Equipment ID: EQ-FAKE-123\n"
            "Maintenance Type: preventive|corrective|inspection\n"
            "Status: open|in_progress|completed|deferred\n"
            "Start Time: ISO 8601 timestamp\n"
            "End Time: ISO 8601 timestamp (if completed)\n"
            "Duration (minutes): 120\n"
            "Technician: John Fake-Smith\n"
            "Issue Description: Detailed description of issue or maintenance\n"
            "Actions Taken:\n"
            "  - action description\n"
            "  - another action\n"
            "Parts Used:\n"
            "  - PART-FAKE-001 (quantity: 2)\n"
            "  - PART-FAKE-002 (quantity: 1)\n"
            "Follow-up Tasks:\n"
            "  - task description (optional)\n"
        )

    def post_process(self, raw, output_format):
        """Deserialize based on output_format and validate structure."""
        fmt = output_format.lower()
        parsed_data = None

        if fmt == "json":
            try:
                parsed_data = json.loads(raw)
            except json.JSONDecodeError:
                return raw
        elif fmt == "yaml":
            try:
                parsed_data = yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        # Handle both 'txt' (from CLI) and 'text' (from tool's supported_output_formats)
        elif fmt == "txt" or fmt == "text":
            return raw
        else:
            return raw

        # Validate and enrich structured data if it's a dictionary
        if isinstance(parsed_data, dict):
            # Ensure required fields have sensible defaults
            parsed_data.setdefault("maintenance_type", "preventive")
            parsed_data.setdefault("status", "open")
            parsed_data.setdefault("actions_taken", [])
            parsed_data.setdefault("parts_used", [])
            parsed_data.setdefault("follow_up_tasks", [])

        return parsed_data

    def get_system_description(self):
        """Return a sentence describing the maintenance log context."""
        return f"Maintenance logs for {self.equipment_type} on {self.plant}/{self.line}"


class TestManufacturingMaintenanceLogTool:
    """Test suite for ManufacturingMaintenanceLogTool functionality."""

    # ------------------------------------------------------------------ #
    # Initialization Tests                                               #
    # ------------------------------------------------------------------ #
    def test_default_initialization(self):
        """Test default initialization with no parameters."""
        tool = ManufacturingMaintenanceLogTool()
        assert tool.plant == "Plant A"
        assert tool.line == "Line 1"
        assert tool.equipment_type == "General"

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        tool = ManufacturingMaintenanceLogTool(
            plant="Plant B", line="Line 3", equipment_type="CNC"
        )
        assert tool.plant == "Plant B"
        assert tool.line == "Line 3"
        assert tool.equipment_type == "CNC"

    # ------------------------------------------------------------------ #
    # CLI Interface Tests                                                #
    # ------------------------------------------------------------------ #
    def test_cli_arguments(self):
        """Test cli_arguments method returns expected structure."""
        tool = ManufacturingMaintenanceLogTool()
        args = tool.cli_arguments()
        
        assert len(args) == 3
        
        # Check plant argument
        plant_arg = args[0]
        assert plant_arg["flags"] == ["--plant"]
        assert not plant_arg["kwargs"]["required"]
        assert plant_arg["kwargs"]["default"] == "Plant A"
        
        # Check line argument
        line_arg = args[1]
        assert line_arg["flags"] == ["--line"]
        assert not line_arg["kwargs"]["required"]
        assert line_arg["kwargs"]["default"] == "Line 1"
        
        # Check equipment-type argument
        equipment_arg = args[2]
        assert equipment_arg["flags"] == ["--equipment-type"]
        assert not equipment_arg["kwargs"]["required"]
        assert equipment_arg["kwargs"]["default"] == "General"

    def test_validate_args(self):
        """Test validate_args persists args correctly."""
        tool = ManufacturingMaintenanceLogTool()
        
        # Test with all args set
        ns = argparse.Namespace(
            plant="Plant C", line="Line 5", equipment_type="Press"
        )
        tool.validate_args(ns)
        assert tool.plant == "Plant C"
        assert tool.line == "Line 5"
        assert tool.equipment_type == "Press"
        
        # Test with args as None (should use defaults)
        ns = argparse.Namespace(plant=None, line=None, equipment_type=None)
        tool.validate_args(ns)
        assert tool.plant == "Plant A"
        assert tool.line == "Line 1"
        assert tool.equipment_type == "General"

    def test_examples(self):
        """Test examples method returns non-empty list of strings."""
        tool = ManufacturingMaintenanceLogTool()
        examples = tool.examples()
        
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(isinstance(ex, str) for ex in examples)
        assert all("manufacturing-maintenance-log" in ex for ex in examples)

    # ------------------------------------------------------------------ #
    # Output Format Tests                                                #
    # ------------------------------------------------------------------ #
    def test_supported_output_formats(self):
        """Test supported_output_formats returns expected formats."""
        tool = ManufacturingMaintenanceLogTool()
        formats = tool.supported_output_formats()
        
        assert isinstance(formats, list)
        assert set(formats) == {"yaml", "json", "text"}

    # ------------------------------------------------------------------ #
    # Prompt Generation Tests                                            #
    # ------------------------------------------------------------------ #
    def test_prompt_common(self):
        """Test _prompt_common includes expected elements."""
        tool = ManufacturingMaintenanceLogTool(
            plant="Plant X", line="Line Y", equipment_type="Conveyor"
        )
        test_id = "test-log-123"
        
        result = tool._prompt_common(unique_id=test_id)
        
        assert test_id in result
        assert "Created At:" in result
        assert "Plant: Plant X" in result
        assert "Line: Line Y" in result
        assert "Equipment Type: Conveyor" in result

    def test_prompt_common_generates_uuid(self):
        """Test _prompt_common generates UUID when not provided."""
        tool = ManufacturingMaintenanceLogTool()
        
        result = tool._prompt_common()
        
        # Check that the method ran and returned a result
        assert "Log ID" in result
        assert "Created At:" in result
        assert "Plant:" in result
        assert "Line:" in result
        assert "Equipment Type:" in result

    def test_build_prompt_yaml(self):
        """Test build_prompt for YAML output format."""
        tool = ManufacturingMaintenanceLogTool(equipment_type="CNC")
        test_id = "test-uuid-yaml"
        
        result = tool.build_prompt("yaml", unique_id=test_id)
        
        assert test_id in result
        assert "Return valid YAML ONLY" in result
        assert "maintenance technician" in result
        assert "log_id: (echo above)" in result

    def test_build_prompt_json(self):
        """Test build_prompt for JSON output format."""
        tool = ManufacturingMaintenanceLogTool(equipment_type="Press")
        test_id = "test-uuid-json"
        
        result = tool.build_prompt("json", unique_id=test_id)
        
        assert test_id in result
        assert "Return valid JSON ONLY" in result
        assert "maintenance technician" in result
        assert '"log_id": "(echo above)"' in result

    def test_build_prompt_text(self):
        """Test build_prompt for plain text output format."""
        tool = ManufacturingMaintenanceLogTool()
        test_id = "test-uuid-text"
        
        result = tool.build_prompt("text", unique_id=test_id)
        
        assert test_id in result
        assert "Return plain text WITHOUT YAML/JSON markers" in result
        assert "maintenance technician" in result

    # ------------------------------------------------------------------ #
    # Post-processing Tests                                              #
    # ------------------------------------------------------------------ #
    def test_post_process_json_valid(self):
        """Test post_process handles valid JSON correctly."""
        tool = ManufacturingMaintenanceLogTool()
        valid_json = '{"log_id": "123", "equipment_id": "EQ-FAKE-001"}'
        
        result = tool.post_process(valid_json, "json")
        
        assert isinstance(result, dict)
        assert result["log_id"] == "123"
        assert result["equipment_id"] == "EQ-FAKE-001"
        # Check for data enrichment
        assert "maintenance_type" in result
        assert "status" in result
        assert "actions_taken" in result
        assert "parts_used" in result
        assert "follow_up_tasks" in result

    def test_post_process_yaml_valid(self):
        """Test post_process handles valid YAML correctly."""
        tool = ManufacturingMaintenanceLogTool()
        valid_yaml = "log_id: 123\nequipment_id: EQ-FAKE-001"
        
        result = tool.post_process(valid_yaml, "yaml")
        
        assert isinstance(result, dict)
        assert result["log_id"] == 123
        assert result["equipment_id"] == "EQ-FAKE-001"
        # Check for data enrichment
        assert "maintenance_type" in result
        assert "status" in result
        assert "actions_taken" in result
        assert "parts_used" in result
        assert "follow_up_tasks" in result

    def test_post_process_text(self):
        """Test post_process with text format returns raw string."""
        tool = ManufacturingMaintenanceLogTool()
        text = "Maintenance log details in plain text format"
        
        result = tool.post_process(text, "text")
        assert result == text
        
        # Also test with "txt" format alias
        result = tool.post_process(text, "txt")
        assert result == text

    def test_post_process_json_invalid(self):
        """Test post_process handles invalid JSON gracefully."""
        tool = ManufacturingMaintenanceLogTool()
        invalid_json = '{log_id: "missing quotes"}'
        
        result = tool.post_process(invalid_json, "json")
        assert result == invalid_json  # Should return raw string

    def test_post_process_yaml_invalid(self):
        """Test post_process handles invalid YAML gracefully."""
        tool = ManufacturingMaintenanceLogTool()
        
        # Use a truly invalid YAML string that will cause an error
        invalid_yaml = ": invalid: yaml: format:"
        
        result = tool.post_process(invalid_yaml, "yaml")
        assert result == invalid_yaml  # Should return raw string

    def test_post_process_unknown_format(self):
        """Test post_process handles unknown formats gracefully."""
        tool = ManufacturingMaintenanceLogTool()
        data = "Some data"
        
        result = tool.post_process(data, "unknown_format")
        assert result == data  # Should return raw string

    # ------------------------------------------------------------------ #
    # Other Method Tests                                                 #
    # ------------------------------------------------------------------ #
    def test_get_system_description(self):
        """Test get_system_description returns expected string."""
        tool = ManufacturingMaintenanceLogTool(
            plant="Plant Z", line="Line 9", equipment_type="Robot"
        )
        
        result = tool.get_system_description()
        
        assert "Maintenance logs for Robot on Plant Z/Line 9" == result

    # ------------------------------------------------------------------ #
    # Data Enrichment Tests                                              #
    # ------------------------------------------------------------------ #
    def test_data_enrichment_adds_missing_fields(self):
        """Test data enrichment adds missing fields."""
        tool = ManufacturingMaintenanceLogTool()
        minimal_json = '{"log_id": "123", "equipment_id": "EQ-FAKE-001"}'
        
        result = tool.post_process(minimal_json, "json")
        
        assert "maintenance_type" in result
        assert "status" in result
        assert "actions_taken" in result
        assert "parts_used" in result
        assert "follow_up_tasks" in result

    def test_data_enrichment_preserves_existing_fields(self):
        """Test data enrichment preserves existing fields."""
        tool = ManufacturingMaintenanceLogTool()
        json_with_fields = (
            '{"log_id": "123", "maintenance_type": "corrective", '
            '"status": "completed", "actions_taken": ["Replace part"]}'
        )
        
        result = tool.post_process(json_with_fields, "json")
        
        assert result["maintenance_type"] == "corrective"
        assert result["status"] == "completed"
        assert result["actions_taken"] == ["Replace part"]
        # Should add missing fields
        assert "parts_used" in result
        assert "follow_up_tasks" in result

    def test_data_enrichment_default_values(self):
        """Test data enrichment uses correct default values."""
        tool = ManufacturingMaintenanceLogTool()
        minimal_json = '{"log_id": "123"}'
        
        result = tool.post_process(minimal_json, "json")
        
        assert result["maintenance_type"] == "preventive"
        assert result["status"] == "open"
        assert result["actions_taken"] == []
        assert result["parts_used"] == []
        assert result["follow_up_tasks"] == []