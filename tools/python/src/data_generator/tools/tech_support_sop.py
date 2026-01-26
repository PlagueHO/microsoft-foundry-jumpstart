"""
Tech-Support Standard Operating Procedure (SOP) Generator
==========================================================

Scenario-specific implementation of :class:`data_generator.tool.DataGeneratorTool`
that creates realistic (but fully fictional) standard operating procedure documents
for fixing common tech support problems.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any

import yaml

from ..tool import DataGeneratorTool

_logger = logging.getLogger(__name__)


class TechSupportSOPTool(DataGeneratorTool):
    """
    Generate synthetic tech support standard operating procedure documents.

    Supports YAML, JSON or plain-text output formats.
    """

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "tech-support-sop"
    toolName: str = "TechSupportSOP"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        problem_category: str | None = None,
        complexity: str | None = None,
        system_context: str | None = None,
    ) -> None:
        """Instantiate the tool, optionally overriding defaults."""
        super().__init__()
        self.problem_category = problem_category or "general"
        self.complexity = complexity or "medium"
        self.system_context = system_context or "Generic enterprise IT environment"

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--problem-category"],
                "kwargs": {
                    "choices": [
                        "general",
                        "network",
                        "application",
                        "authentication",
                        "hardware",
                        "database",
                        "cloud",
                        "security",
                    ],
                    "default": "general",
                    "help": (
                        "Category of tech support problem "
                        "(e.g., network, application)"
                    ),
                },
            },
            {
                "flags": ["--complexity"],
                "kwargs": {
                    "choices": ["simple", "medium", "complex"],
                    "default": "medium",
                    "help": "Complexity level of the SOP (simple, medium, complex)",
                },
            },
            {
                "flags": ["--system-context"],
                "kwargs": {
                    "default": "Generic enterprise IT environment",
                    "help": "System or environment context for the SOP",
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate mandatory arguments after CLI parsing."""
        # Store CLI args
        self.problem_category = getattr(ns, "problem_category", "general")
        self.complexity = getattr(ns, "complexity", "medium")
        self.system_context = getattr(
            ns, "system_context", "Generic enterprise IT environment"
        )

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario tech-support-sop "
            "--count 20 "
            "--problem-category network "
            '--system-context "Azure cloud environment" '
            "--output-format yaml",
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:  # noqa: D401
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "txt", "text"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    _SEVERITY: list[str] = ["critical", "high", "medium", "low"]
    _STATUS: list[str] = ["draft", "review", "approved", "published", "archived"]
    _APPROVAL_LEVELS: list[str] = ["team_lead", "manager", "director", "cto"]

    def _random_attributes(self) -> tuple[str, str, str]:
        """Randomly choose severity, status, and approval level values."""
        return (
            random.choice(self._SEVERITY),
            random.choice(self._STATUS),
            random.choice(self._APPROVAL_LEVELS),
        )

    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Return the invariant part of the prompt shared across formats."""
        severity, status, approval_level = self._random_attributes()
        sop_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        version = f"1.{random.randint(0, 9)}"

        return (
            f"SOP ID (immutable): {sop_id}\n"
            f"Created At: {created_at}\n"
            f"Version: {version}\n"
            f"Problem Category: {self.problem_category}\n"
            f"Complexity: {self.complexity}\n"
            f"System Context: {self.system_context}\n"
            f"Severity: {severity}\n"
            f"Status: {status}\n"
            f"Approval Level: {approval_level}\n"
            "Use ISO-8601 timestamps and do NOT invent real PII.\n\n"
        )

    def build_prompt(
        self, output_format: str, *, unique_id: str | None = None
    ) -> str:  # noqa: D401
        """
        Construct the full system-prompt string for the requested *output_format*.
        All variable data (status, ids, etc.) are pre-baked so the kernel only
        receives the `index` placeholder supplied by the engine.
        """
        # Normalize output format for text variations
        fmt = output_format.lower()
        if fmt == "text":
            fmt = "txt"

        base = (
            "You are a helpful technical documentation specialist "
            "generating REALISTIC BUT ENTIRELY FICTIONAL standard operating "
            "procedure (SOP) documents for tech support teams.\n\n"
            "## ON THE SOP\n\n"
            f"Problem category: {self.problem_category}\n"
            f"Complexity level: {self.complexity}\n"
            f"System context: {self.system_context}\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "## ON SOP CONTENT\n\n"
            "SOPs should include:\n"
            "- Clear problem description and symptoms\n"
            "- Prerequisites and required tools/access\n"
            "- Step-by-step resolution procedures with realistic technical details\n"
            "- Verification steps to confirm the issue is resolved\n"
            "- Troubleshooting tips for common issues\n"
            "- Escalation procedures if the SOP doesn't resolve the problem\n"
            "- Related documentation and knowledge base articles\n"
            "- Version history with realistic change descriptions\n"
            "All technical details must be realistic but entirely fictional.\n"
        )

        if fmt == "yaml":
            return base + self._yaml_skeleton()
        if fmt == "json":
            return base + self._json_skeleton()
        # Plain text is the default
        return base + self._text_skeleton()

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _yaml_skeleton() -> str:
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID YAML ONLY (no markdown fences).\n\n"
            "sop_id: (echo above)\n"
            "version: (echo above)\n"
            "created_at: (echo above)\n"
            "last_updated: ISO 8601\n"
            "title: clear descriptive title\n"
            "problem_category: (echo above)\n"
            "complexity: simple|medium|complex\n"
            "system_context: (echo above)\n"
            "severity: critical|high|medium|low\n"
            "status: draft|review|approved|published|archived\n"
            "approval_level: team_lead|manager|director|cto\n"
            "author:\n"
            "  name: fictional name\n"
            "  email: realistic but fake email\n"
            "approver:\n"
            "  name: fictional name (optional)\n"
            "  email: realistic but fake email (optional)\n"
            "  approved_at: ISO 8601 (optional)\n"
            "problem_description: detailed description of the problem\n"
            "symptoms:\n"
            "  - symptom description\n"
            "prerequisites:\n"
            "  - prerequisite item\n"
            "required_tools:\n"
            "  - tool or access requirement\n"
            "estimated_resolution_time: text (e.g., '15-30 minutes')\n"
            "resolution_steps:\n"
            "  - step_number: 1\n"
            "    action: text\n"
            "    details: text\n"
            "    warnings: text (optional)\n"
            "verification_steps:\n"
            "  - step: text\n"
            "troubleshooting:\n"
            "  - issue: text\n"
            "    solution: text\n"
            "escalation:\n"
            "  condition: text\n"
            "  contact: text\n"
            "  escalation_path: text\n"
            "related_documentation:\n"
            "  - title: text\n"
            "    url: fictional but realistic URL\n"
            "tags:\n"
            "  - tag text\n"
            "version_history:\n"
            "  - version: text\n"
            "    date: ISO 8601\n"
            "    author: text\n"
            "    changes: text\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "sop_id": "(echo above)",\n'
            '  "version": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "last_updated": "ISO 8601",\n'
            '  "title": "clear descriptive title",\n'
            '  "problem_category": "(echo above)",\n'
            '  "complexity": "simple|medium|complex",\n'
            '  "system_context": "(echo above)",\n'
            '  "severity": "critical|high|medium|low",\n'
            '  "status": "draft|review|approved|published|archived",\n'
            '  "approval_level": "team_lead|manager|director|cto",\n'
            '  "author": {\n'
            '    "name": "fictional name",\n'
            '    "email": "realistic but fake email"\n'
            '  },\n'
            '  "approver": {\n'
            '    "name": "fictional name (optional)",\n'
            '    "email": "realistic but fake email (optional)",\n'
            '    "approved_at": "ISO 8601 (optional)"\n'
            '  },\n'
            '  "problem_description": "detailed description of the problem",\n'
            '  "symptoms": ["symptom description"],\n'
            '  "prerequisites": ["prerequisite item"],\n'
            '  "required_tools": ["tool or access requirement"],\n'
            '  "estimated_resolution_time": "text (e.g., \'15-30 minutes\')",\n'
            '  "resolution_steps": [\n'
            '    {\n'
            '      "step_number": 1,\n'
            '      "action": "text",\n'
            '      "details": "text",\n'
            '      "warnings": "text (optional)"\n'
            '    }\n'
            '  ],\n'
            '  "verification_steps": [{"step": "text"}],\n'
            '  "troubleshooting": [\n'
            '    {\n'
            '      "issue": "text",\n'
            '      "solution": "text"\n'
            '    }\n'
            '  ],\n'
            '  "escalation": {\n'
            '    "condition": "text",\n'
            '    "contact": "text",\n'
            '    "escalation_path": "text"\n'
            '  },\n'
            '  "related_documentation": [\n'
            '    {\n'
            '      "title": "text",\n'
            '      "url": "fictional but realistic URL"\n'
            '    }\n'
            '  ],\n'
            '  "tags": ["tag text"],\n'
            '  "version_history": [\n'
            '    {\n'
            '      "version": "text",\n'
            '      "date": "ISO 8601",\n'
            '      "author": "text",\n'
            '      "changes": "text"\n'
            '    }\n'
            '  ]\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "SOP ID: (echo above)\n"
            "Version: (echo above)\n"
            "Created At: (echo above)\n"
            "Last Updated: ISO 8601\n"
            "Title: clear descriptive title\n"
            "Problem Category: (echo above)\n"
            "Complexity: simple|medium|complex\n"
            "System Context: (echo above)\n"
            "Severity: critical|high|medium|low\n"
            "Status: draft|review|approved|published|archived\n"
            "Approval Level: team_lead|manager|director|cto\n"
            "Author: fictional name <realistic but fake email>\n"
            "Approver: fictional name <realistic but fake email> (optional)\n"
            "Approved At: ISO 8601 (optional)\n\n"
            "PROBLEM DESCRIPTION:\n"
            "detailed description of the problem\n\n"
            "SYMPTOMS:\n"
            "- symptom description\n\n"
            "PREREQUISITES:\n"
            "- prerequisite item\n\n"
            "REQUIRED TOOLS:\n"
            "- tool or access requirement\n\n"
            "ESTIMATED RESOLUTION TIME: text (e.g., '15-30 minutes')\n\n"
            "RESOLUTION STEPS:\n"
            "1. Action: text\n"
            "   Details: text\n"
            "   Warnings: text (optional)\n\n"
            "VERIFICATION STEPS:\n"
            "- step description\n\n"
            "TROUBLESHOOTING:\n"
            "Issue: text\n"
            "Solution: text\n\n"
            "ESCALATION:\n"
            "Condition: text\n"
            "Contact: text\n"
            "Escalation Path: text\n\n"
            "RELATED DOCUMENTATION:\n"
            "- Title: text\n"
            "  URL: fictional but realistic URL\n\n"
            "TAGS: tag1, tag2, tag3\n\n"
            "VERSION HISTORY:\n"
            "Version: text | Date: ISO 8601 | Author: text | Changes: text\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format; fallback to raw string on failure."""
        fmt = output_format.lower()
        # Handle both 'txt' and 'text' variations
        if fmt in ("txt", "text"):
            return raw
        if fmt == "json" and raw.lstrip().startswith("{"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        if fmt == "yaml" and ":" in raw and "\n" in raw:  # naive YAML sniff
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
        """Return the current system description string."""
        return (
            f"Tech support SOP for {self.problem_category} problems "
            f"in {self.system_context}"
        )
