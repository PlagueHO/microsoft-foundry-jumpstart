"""
Manufacturing Maintenance Log Prompt Builder
=============================================

Concrete :class:`data_generator.tool.DataGeneratorTool` implementation that
creates realistic manufacturing maintenance log entries.
"""

from __future__ import annotations

import argparse
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import yaml

from ..tool import DataGeneratorTool

_logger = logging.getLogger(__name__)


class ManufacturingMaintenanceLogTool(DataGeneratorTool):
    """Generate synthetic manufacturing maintenance log entries."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "manufacturing-maintenance-log"
    toolName: str = "ManufacturingMaintenanceLog"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        plant: str | None = None,
        line: str | None = None,
        equipment_type: str | None = None,
    ) -> None:
        """Create a new tool instance with optional overrides."""
        super().__init__()
        self.plant = plant or "Plant A"
        self.line = line or "Line 1"
        self.equipment_type = equipment_type or "General"

    def cli_arguments(self) -> list[dict[str, Any]]:
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

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Persist validated CLI arguments onto the instance."""
        self.plant = ns.plant or "Plant A"
        self.line = ns.line or "Line 1"
        self.equipment_type = ns.equipment_type or "General"

    def examples(self) -> list[str]:
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

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "text"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    def _prompt_common(self, *, unique_id: str | None = None) -> str:
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

    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        """Return the full prompt for the requested *output_format*."""
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

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    def _yaml_skeleton(self) -> str:
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

    def _json_skeleton(self) -> str:
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
    def _text_skeleton() -> str:
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

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format and validate structure."""
        fmt = output_format.lower()
        parsed_data: Any

        if fmt == "json":
            try:
                parsed_data = json.loads(raw)
            except json.JSONDecodeError:
                _logger.warning(
                    "Failed to parse raw output as JSON. Returning raw string."
                )
                return raw
        elif fmt == "yaml":
            try:
                parsed_data = yaml.safe_load(raw)
            except yaml.YAMLError:
                _logger.warning(
                    "Failed to parse raw output as YAML. Returning raw string."
                )
                return raw
        # Handle both 'txt' (from CLI) and 'text' (from tool's supported_output_formats)
        elif fmt in ("txt", "text"):
            return raw
        else:
            _logger.warning(
                "Unknown output format '%s' for post-processing. Returning raw string.",
                output_format,
            )
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

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Return a sentence describing the maintenance log context."""
        return f"Maintenance logs for {self.equipment_type} on {self.plant}/{self.line}"
