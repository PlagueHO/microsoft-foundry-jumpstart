"""
HR Employee Record Data Generator.

This module provides a tool to generate synthetic HR employee record data
for testing and development purposes. Supports various output formats including
JSON, YAML, and text.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import yaml

from ..tool import DataGeneratorTool


class HREmployeeRecordTool(DataGeneratorTool):
    """Generate synthetic HR employee records in YAML, JSON or plain-text."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "hr-employee-record"
    toolName: str = "HREmployeeRecord"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self, *, record_type: str | None = None, department: str | None = None
    ) -> None:
        """Instantiate with optional record type and department."""
        super().__init__()
        self.record_type = record_type or "onboarding"
        self.department = department or "General"

    def cli_arguments(self) -> list[dict[str, Any]]:
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

    def validate_args(self, ns: argparse.Namespace) -> None:
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

    def examples(self) -> list[str]:
        """Usage examples for help text."""
        return [
            "python -m generate_data "
            "--scenario hr-employee-record "
            "--count 20 "
            "--record-type performance "
            "--department Sales "
            "--output-format json"
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:
        """Return supported output formats."""
        return ["yaml", "json", "text"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Common header with record ID and timestamp."""
        record_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Record ID: {record_id}\n"
            f"Created At: {created_at}\n"
            f"Record Type: {self.record_type}\n"
            f"Department: {self.department}\n\n"
        )

    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
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

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _yaml_skeleton() -> str:
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
    def _json_skeleton() -> str:
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
    def _text_skeleton() -> str:
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

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:
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

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Provide a brief description of this tool's context."""
        return f"HR employee records ({self.record_type}, {self.department})"
