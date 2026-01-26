"""
Healthcare Record Data Generator.

This module provides a tool to generate synthetic healthcare record data
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


class HealthcareRecordTool(DataGeneratorTool):
    """Generate synthetic healthcare records in YAML, JSON or plain-text."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "healthcare-record"
    toolName: str = "HealthcareRecord"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self, *, document_type: str | None = None, specialty: str | None = None
    ) -> None:
        """Instantiate with optional document type and specialty."""
        super().__init__()
        self.document_type = document_type or "Clinic Note"
        self.specialty = specialty or "General Medicine"

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Define scenario-specific CLI flags."""
        return [
            {
                "flags": ["--document-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "Clinic Note",
                    "help": (
                        "Type of medical document (e.g. Clinic Note, Discharge Summary)"
                    ),
                },
            },
            {
                "flags": ["--specialty"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "General Medicine",
                    "help": (
                        "Medical specialty for the record (e.g. Cardiology, Oncology)."
                    ),
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Persist and validate CLI args."""
        self.document_type = ns.document_type or self.document_type
        self.specialty = ns.specialty or self.specialty

    def examples(self) -> list[str]:
        """Usage examples for help text."""
        return [
            "python -m generate_data "
            "--scenario healthcare-record "
            "--count 10 "
            "--document-type \"Discharge Summary\" "
            "--specialty Cardiology "
            "--output-format yaml"
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
            f"Document Type: {self.document_type}\n"
            f"Specialty: {self.specialty}\n"
            f"Created At: {created_at}\n\n"
        )

    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        """Assemble the full LLM prompt for the desired format."""
        base = (
            "You are an AI assistant generating realistic but entirely FICTIONAL "
            "and ANONYMIZED healthcare documents. No real PII.\n\n"
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
            "document_type: (echo above)\n"
            "specialty: (echo above)\n"
            "created_at: (echo above)\n"
            "patient_details:\n"
            "  fictional_name: \"Fictional Patient Name\"\n"
            "  age: integer\n"
            "  gender: \"Male|Female|Other\"\n"
            "  fictional_patient_id: \"Fake ID\"\n"
            "document_content:\n"
            "  title: \"Document title\"\n"
            "  sections:\n"
            "    - heading: text\n"
            "      content: text\n"
            "author_details:\n"
            "  fictional_doctor_name: \"Dr. Fictional\"\n"
            "  fictional_clinic_name: \"Fictional Clinic\"\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON schema instructions."""
        return (
            "Return VALID JSON ONLY (no fences).\n\n"
            "{\n"
            '  "record_id": "(echo above)",\n'
            '  "document_type": "(echo above)",\n'
            '  "specialty": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "patient_details": {\n'
            '    "fictional_name": "Fictional Patient Name",\n'
            '    "age": 35,\n'
            '    "gender": "Female",\n'
            '    "fictional_patient_id": "MRN-FAKE-12345"\n'
            "  },\n"
            '  "document_content": {\n'
            '    "title": "Title",\n'
            '    "sections": [ { "heading": "…", "content": "…" } ]\n'
            "  },\n"
            '  "author_details": {\n'
            '    "fictional_doctor_name": "Dr. Fictional",\n'
            '    "fictional_clinic_name": "Fictional Clinic"\n'
            "  }\n"
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text format guidelines."""
        return (
            "Return plain text WITHOUT YAML/JSON markers.\n\n"
            "Record ID: (echo above)\n"
            "Document Type: (echo above)\n"
            "Specialty: (echo above)\n"
            "Created At: (echo above)\n"
            "Patient Details: Fictional Name, Age, Gender, Fake ID\n"
            "Document Content: Title and sectioned paragraphs\n"
            "Author Details: Dr. Fictional, Fictional Clinic\n"
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
        # plain-text or unrecognized format
        return raw

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Provide a brief description of this tool’s context."""
        return f"Healthcare records ({self.document_type}, {self.specialty})"
