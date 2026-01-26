"""
Customer Support Chat Log Prompt Builder
========================================

Scenario-specific implementation of :class:`data_generator.tool.DataGeneratorTool`
that creates realistic (but fully fictional) customer support chat logs with
multi-turn conversations between customers and support agents.
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


class CustomerSupportChatLogTool(DataGeneratorTool):
    """Generate synthetic customer support chat logs in YAML, JSON or plain-text."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "customer-support-chat-log"
    toolName: str = "CustomerSupportChatLog"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        industry: str | None = None,
        avg_turns: int | None = None,
        languages: str | None = None
    ) -> None:
        """Instantiate the tool with optional parameters."""
        super().__init__()
        self.industry = industry or "general"
        self.avg_turns = avg_turns or 8
        self.languages = languages or "en"

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--industry"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "general",
                    "help": (
                        "Industry for the customer support context "
                        "(e.g., telecom, banking, retail)."
                    ),
                },
            },
            {
                "flags": ["--avg-turns"],
                "kwargs": {
                    "required": False,
                    "type": int,
                    "metavar": "INT",
                    "default": 8,
                    "help": (
                        "Average number of total messages per conversation "
                        "(customer + agent). Range: 2-50."
                    ),
                },
            },
            {
                "flags": ["--languages"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "en",
                    "help": (
                        "Comma-separated ISO language codes for conversation "
                        "content (e.g., 'en', 'en,es,fr')."
                    ),
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate and normalize CLI arguments after parsing."""
        # Store validated arguments
        self.industry = getattr(ns, "industry", None) or "general"
        self.languages = getattr(ns, "languages", None) or "en"

        # Validate and clamp avg_turns
        avg_turns = getattr(ns, "avg_turns", None) or 8
        if not isinstance(avg_turns, int):
            try:
                avg_turns = int(avg_turns)
            except (ValueError, TypeError):
                avg_turns = 8
        # Clamp to valid range [2, 50]
        self.avg_turns = max(2, min(50, avg_turns))

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario customer-support-chat-log "
            "--count 50 "
            "--industry telecom "
            "--avg-turns 10 "
            "--languages en,es "
            "--output-format yaml",
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
    _CHANNELS: list[str] = ["email", "chat", "phone"]
    _RESOLUTION_STATUS: list[str] = ["open", "in_progress", "resolved", "escalated"]
    _SENTIMENT: list[str] = ["positive", "neutral", "negative"]

    def _random_channel(self) -> str:
        """Return a random communication channel."""
        return random.choice(self._CHANNELS)

    def _random_resolution_status(self) -> str:
        """Return a random resolution status."""
        return random.choice(self._RESOLUTION_STATUS)

    def _select_language(self) -> str:
        """Select one language from the configured languages list."""
        lang_list = [lang.strip() for lang in self.languages.split(",")]
        return random.choice(lang_list)

    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Return the invariant part of the prompt shared across formats."""
        conversation_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        language = self._select_language()

        return (
            f"Conversation ID (immutable): {conversation_id}\n"
            f"Created At: {created_at}\n"
            f"Industry: {self.industry}\n"
            f"Language: {language}\n"
            f"Average Turns Hint: {self.avg_turns}\n"
            "Use ISO-8601 timestamps and do NOT invent real PII.\n\n"
        )

    def build_prompt(
        self, output_format: str, *, unique_id: str | None = None
    ) -> str:
        """
        Construct the full system-prompt string for the requested *output_format*.
        All variable data (conversation_id, timestamps, etc.) are pre-baked so
        the kernel only receives the final prompt.
        """
        base = (
            "You are a helpful assistant generating REALISTIC BUT ENTIRELY "
            "FICTIONAL multi-turn customer support chat logs for demonstrations.\n\n"
            "## CONVERSATION DETAILS\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "## CONVERSATION GUIDELINES\n\n"
            "Generate a realistic customer support conversation with occasional "
            "ambiguity, realistic product or service references, timestamps per "
            "message, and no real PII. Customer messages should reflect real issues "
            "people might have, and agent responses should be helpful and "
            "professional. "
            f"Target approximately {self.avg_turns} total messages but this can vary "
            "naturally.\n\n"
            "Return ONLY the requested format (no markdown fences).\n\n"
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
    def _yaml_skeleton(self) -> str:
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID YAML ONLY (no markdown fences).\n\n"
            "conversation_id: (echo above)\n"
            "created_at: (echo above)\n"
            "industry: (echo above)\n"
            "language: (echo above)\n"
            "issue_summary: single sentence describing the customer's issue\n"
            "customer_profile:\n"
            "  name: realistic but fictional name\n"
            "  email: realistic but fake email address\n"
            "  plan_tier: e.g., basic, premium, enterprise\n"
            "messages:\n"
            "  - role: customer|agent\n"
            "    message: conversation text\n"
            "    timestamp: ISO 8601\n"
            "    channel: email|chat|phone\n"
            "    sentiment: positive|neutral|negative\n"
            "resolution_status: open|in_progress|resolved|escalated\n"
            "resolution_summary: optional text summary (if resolved)\n"
        )

    def _json_skeleton(self) -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "conversation_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "industry": "(echo above)",\n'
            '  "language": "(echo above)",\n'
            '  "issue_summary": "single sentence describing the customer\'s issue",\n'
            '  "customer_profile": {\n'
            '    "name": "realistic but fictional name",\n'
            '    "email": "realistic but fake email address",\n'
            '    "plan_tier": "basic|premium|enterprise"\n'
            '  },\n'
            '  "messages": [\n'
            '    {\n'
            '      "role": "customer|agent",\n'
            '      "message": "conversation text",\n'
            '      "timestamp": "ISO 8601",\n'
            '      "channel": "email|chat|phone",\n'
            '      "sentiment": "positive|neutral|negative"\n'
            '    }\n'
            '  ],\n'
            '  "resolution_status": "open|in_progress|resolved|escalated",\n'
            '  "resolution_summary": "optional text summary (if resolved)"\n'
            "}\n"
        )

    def _text_skeleton(self) -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Conversation ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Industry: (echo above)\n"
            "Language: (echo above)\n"
            "Issue Summary: single sentence describing the customer's issue\n"
            "Customer Profile:\n"
            "  Name: realistic but fictional name\n"
            "  Email: realistic but fake email address\n"
            "  Plan Tier: basic|premium|enterprise\n"
            "Conversation History:\n"
            "  timestamp [customer/channel] message (sentiment)\n"
            "  timestamp [agent/channel] message (sentiment)\n"
            "Resolution Status: open|in_progress|resolved|escalated\n"
            "Resolution Summary: optional text summary (if resolved)\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format; fallback to raw string on failure."""
        fmt = output_format.lower()

        if fmt == "json":
            try:
                parsed_data = json.loads(raw)
                if isinstance(parsed_data, dict):
                    # Optional enrichment: ensure basic fields exist
                    parsed_data.setdefault(
                        "resolution_status", self._random_resolution_status()
                    )
                return parsed_data
            except json.JSONDecodeError:
                _logger.debug(
                    "Failed to parse JSON; returning raw string", exc_info=True
                )
                return raw

        if fmt == "yaml":
            try:
                parsed_data = yaml.safe_load(raw)
                if isinstance(parsed_data, dict):
                    # Optional enrichment: ensure basic fields exist
                    parsed_data.setdefault(
                        "resolution_status", self._random_resolution_status()
                    )
                return parsed_data
            except yaml.YAMLError:
                _logger.debug(
                    "Failed to parse YAML; returning raw string", exc_info=True
                )
                return raw

        # Handle both 'txt' (from CLI) and 'text' (from tool's supported_output_formats)
        if fmt in ("txt", "text"):
            return raw

        # Unknown format
        _logger.warning(
            "Unknown output format '%s'; returning raw string", output_format
        )
        return raw

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Return a descriptive string including industry and languages."""
        languages_str = self.languages.replace(",", ", ")
        return (
            f"Customer support chat logs for {self.industry} "
            f"(languages: {languages_str})"
        )
