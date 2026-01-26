"""
Tech-Support Prompt Builder
===========================

Scenario-specific implementation of :class:`data_generator.tool.DataGeneratorTool`
that creates realistic (but fully fictional) technical-support cases.
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


class TechSupportTool(DataGeneratorTool):
    """Generate synthetic tech-support cases in YAML, JSON or plain-text."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "tech-support"
    toolName: str = "TechSupport"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(self, *, system_description: str | None = None) -> None:
        """Instantiate the tool, optionally overriding *system_description*."""
        super().__init__()
        self.system_description = (
            system_description or "A generic SaaS platform running in Azure."
        )

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["-d", "--system-description"],
                "kwargs": {
                    "required": True,
                    "metavar": "TEXT",
                    "help": (
                        "Short description of the system the support case relates to."
                    ),
                },
            }
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate mandatory arguments after CLI parsing."""
        if not getattr(ns, "system_description", None):
            raise ValueError("--system-description is required.")
        # store for later use
        self.system_description = ns.system_description

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario tech-support "
            "--count 50 "
            '--system-description "ContosoShop - React SPA front-end with '
            'Azure App Service + SQL back-end" '
            "--output-format yaml",
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:  # noqa: D401
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "txt"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    _STATUS:   list[str] = ["open", "investigating", "resolved", "closed"]
    _SEVERITY: list[str] = ["critical", "high", "medium", "low"]
    _PRIORITY: list[str] = ["P1", "P2", "P3", "P4"]

    def _random_attributes(self) -> tuple[str, str, str]:
        """Randomly choose status, severity and priority values."""
        return (
            random.choice(self._STATUS),
            random.choice(self._SEVERITY),
            random.choice(self._PRIORITY),
        )

    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Return the invariant part of the prompt shared across formats."""
        status, severity, priority = self._random_attributes()
        case_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        return (
            f"The status of this case is: {status}\n"
            f"The severity of this case is: {severity}\n"
            f"The priority of this case is: {priority}\n"
            f"Case ID (immutable): {case_id}\n"
            f"Created At: {created_at}\n"
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
        base = (
            "You are a helpful support agent generating REALISTIC BUT ENTIRELY "
            "FICTIONAL technical support cases for demonstrations.\n\n"
            "## ON THE CASE\n\n"
            f"The system being simulated:\n- {self.system_description}\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "## ON CONVERSATION HISTORY\n\n"
            "User messages should be realistic, sometimes unclear, contain realistic "
            "error messages and information. The agent's replies should be helpful "
            "and ask clarifying questions or to provide specific information.\n"
        )

        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
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
            "case_id: (echo above)\n"
            "created_at: (echo above)\n"
            "system_description: (echo above)\n"
            "issue_summary: single sentence summary\n"
            "severity: critical|high|medium|low\n"
            "priority: P1|P2|P3|P4\n"
            "status: open|investigating|resolved|closed\n"
            "customer_name: realistic name\n"
            "contact_email: realistic but fake email\n"
            "conversation_history:\n"
            "  - role: customer|agent\n"
            "    message: text\n"
            "    timestamp: ISO 8601\n"
            "resolved_at: ISO 8601 (optional)\n"
            "resolution: text (optional)\n"
            "area: frontend|backend|database|network|other (optional)\n"
            "is_bug: true|false (optional)\n"
            "root_cause: text (optional)\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "case_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "system_description": "(echo above)",\n'
            '  "issue_summary": "single sentence summary",\n'
            '  "severity": "critical|high|medium|low",\n'
            '  "priority": "P1|P2|P3|P4",\n'
            '  "status": "open|investigating|resolved|closed",\n'
            '  "customer_name": "realistic name",\n'
            '  "contact_email": "realistic but fake email",\n'
            '  "conversation_history": [ '
            '{ "role": "...", "message": "...", "timestamp": "..." } ],\n'
            '  "resolved_at": "ISO 8601 (optional)",\n'
            '  "resolution": "text (optional)",\n'
            '  "area": "frontend|backend|database|network|other (optional)",\n'
            '  "is_bug": true,\n'
            '  "root_cause": "text (optional)"\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Case ID: (echo above)\n"
            "Created At: (echo above)\n"
            "System Description: (echo above)\n"
            "Issue Summary: single sentence summary\n"
            "Severity: critical|high|medium|low\n"
            "Priority: P1|P2|P3|P4\n"
            "Status: open|investigating|resolved|closed\n"
            "Customer Name: realistic name\n"
            "Contact Email: realistic but fake email\n"
            "Conversation History:\n"
            "  - timestamp [customer] message\n"
            "  - timestamp [agent]    message\n"
            "Resolved At: ISO 8601 (optional)\n"
            "Resolution: text (optional)\n"
            "Area: frontend|backend|database|network|other (optional)\n"
            "Is Bug: true|false (optional)\n"
            "Root Cause: text (optional)\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format; fallback to raw string on failure."""
        fmt = output_format.lower()
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
        return self.system_description
