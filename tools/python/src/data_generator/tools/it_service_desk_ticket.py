"""
IT Service Desk Ticket Prompt Builder
=====================================

Scenario-specific implementation of :class:`data_generator.tool.DataGeneratorTool`
that creates realistic (but fully fictional) IT service desk tickets.
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


class ITServiceDeskTicketTool(DataGeneratorTool):
    """Generate synthetic IT service desk tickets in YAML, JSON or plain-text."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "it-service-desk-ticket"
    toolName: str = "ITServiceDeskTicket"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        ticket_type: str | None = None,
        service: str | None = None,
        sla_hours: int | None = None,
    ) -> None:
        """Instantiate the tool, optionally overriding defaults."""
        super().__init__()
        self.ticket_type = ticket_type or "incident"
        self.service = service or "General IT"
        self.sla_hours = sla_hours or 72

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--ticket-type"],
                "kwargs": {
                    "choices": ["incident", "request", "change"],
                    "default": "incident",
                    "help": "Type of IT service desk ticket to generate",
                },
            },
            {
                "flags": ["--service"],
                "kwargs": {
                    "default": "General IT",
                    "help": "Service area for the ticket (e.g., Email, VPN, Laptops)",
                },
            },
            {
                "flags": ["--sla-hours"],
                "kwargs": {
                    "type": int,
                    "default": 72,
                    "help": "Target resolution window in hours",
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate mandatory arguments after CLI parsing."""
        # Store CLI args
        self.ticket_type = getattr(ns, "ticket_type", "incident")
        self.service = getattr(ns, "service", "General IT")
        self.sla_hours = getattr(ns, "sla_hours", 72)

        # Validate and clamp sla_hours to [1, 720]
        if self.sla_hours < 1:
            self.sla_hours = 1
        elif self.sla_hours > 720:
            self.sla_hours = 720

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario it-service-desk-ticket "
            "--count 25 "
            '--service "Email" '
            "--ticket-type incident "
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
    _PRIORITY: list[str] = ["P1", "P2", "P3", "P4"]
    _IMPACT: list[str] = ["high", "medium", "low"]
    _URGENCY: list[str] = ["high", "medium", "low"]
    _STATUS: list[str] = ["new", "assigned", "in_progress", "resolved", "closed"]

    def _random_attributes(self) -> tuple[str, str, str, str]:
        """Randomly choose priority, impact, urgency, and status values."""
        return (
            random.choice(self._PRIORITY),
            random.choice(self._IMPACT),
            random.choice(self._URGENCY),
            random.choice(self._STATUS),
        )

    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Return the invariant part of the prompt shared across formats."""
        priority, impact, urgency, status = self._random_attributes()
        ticket_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        return (
            f"Ticket ID (immutable): {ticket_id}\n"
            f"Created At: {created_at}\n"
            f"Ticket Type: {self.ticket_type}\n"
            f"Service: {self.service}\n"
            f"Priority: {priority}\n"
            f"Impact: {impact}\n"
            f"Urgency: {urgency}\n"
            f"Status: {status}\n"
            f"SLA Hours: {self.sla_hours}\n"
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
            "You are a helpful IT service desk agent generating REALISTIC BUT ENTIRELY "
            "FICTIONAL IT service desk tickets for demonstrations.\n\n"
            "## ON THE TICKET\n\n"
            f"The service area being simulated: {self.service}\n"
            f"Ticket type: {self.ticket_type}\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "## ON TICKET LIFECYCLE\n\n"
            "Tickets should include appropriate fields for the ticket lifecycle "
            "including requester information, work notes with realistic "
            "timestamps and authors, and resolution details when applicable. "
            "All identities must be fictional.\n"
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
            "ticket_id: (echo above)\n"
            "created_at: (echo above)\n"
            "ticket_type: incident|request|change\n"
            "service: (echo above)\n"
            "requester:\n"
            "  name: fictional name\n"
            "  email: realistic but fake email\n"
            "priority: P1|P2|P3|P4\n"
            "impact: high|medium|low\n"
            "urgency: high|medium|low\n"
            "status: new|assigned|in_progress|resolved|closed\n"
            "assignment_group: text\n"
            "assignee: text (optional)\n"
            "description: text\n"
            "work_notes:\n"
            "  - timestamp: ISO 8601\n"
            "    author: text\n"
            "    note: text\n"
            "resolution:\n"
            "  resolved_at: ISO 8601 (optional)\n"
            "  summary: text (optional)\n"
            "sla_hours: (echo above)\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "ticket_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "ticket_type": "incident|request|change",\n'
            '  "service": "(echo above)",\n'
            '  "requester": {\n'
            '    "name": "fictional name",\n'
            '    "email": "realistic but fake email"\n'
            '  },\n'
            '  "priority": "P1|P2|P3|P4",\n'
            '  "impact": "high|medium|low",\n'
            '  "urgency": "high|medium|low",\n'
            '  "status": "new|assigned|in_progress|resolved|closed",\n'
            '  "assignment_group": "text",\n'
            '  "assignee": "text (optional)",\n'
            '  "description": "text",\n'
            '  "work_notes": [\n'
            '    {\n'
            '      "timestamp": "ISO 8601",\n'
            '      "author": "text",\n'
            '      "note": "text"\n'
            '    }\n'
            '  ],\n'
            '  "resolution": {\n'
            '    "resolved_at": "ISO 8601 (optional)",\n'
            '    "summary": "text (optional)"\n'
            '  },\n'
            '  "sla_hours": "(echo above)"\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Ticket ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Ticket Type: incident|request|change\n"
            "Service: (echo above)\n"
            "Requester: fictional name <realistic but fake email>\n"
            "Priority: P1|P2|P3|P4\n"
            "Impact: high|medium|low\n"
            "Urgency: high|medium|low\n"
            "Status: new|assigned|in_progress|resolved|closed\n"
            "Assignment Group: text\n"
            "Assignee: text (optional)\n"
            "Description: text\n"
            "Work Notes:\n"
            "  - [timestamp] author: note\n"
            "Resolution:\n"
            "  Resolved At: ISO 8601 (optional)\n"
            "  Summary: text (optional)\n"
            "SLA Hours: (echo above)\n"
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
        return f"IT service desk tickets for {self.service} ({self.ticket_type})"
