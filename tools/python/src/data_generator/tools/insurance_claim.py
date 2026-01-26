"""
Insurance-Claim Prompt Builder
==============================

Concrete :class:`data_generator.tool.DataGeneratorTool` implementation that
creates realistic yet entirely fictional insurance-claim documents.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import uuid
from datetime import date, timedelta
from typing import Any

import yaml

from ..tool import DataGeneratorTool

_logger = logging.getLogger(__name__)


class InsuranceClaimTool(DataGeneratorTool):
    """Generate synthetic insurance-claim records."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "insurance-claim"
    toolName: str = "InsuranceClaim"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        policy_type: str | None = None,
        fraud_percent: int | None = None,
    ) -> None:
        """Instantiate the tool with optional overrides."""
        super().__init__()
        self.policy_type = policy_type or "auto"
        self.fraud_percent = fraud_percent or 0

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["-p", "--policy-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "auto",
                    "help": "Policy type (auto, home, health).",
                },
            },
            {
                "flags": ["--fraud-percent"],
                "kwargs": {
                    "required": False,
                    "metavar": "P",
                    "type": int,
                    "default": 0,
                    "help": "Percentage chance the claim is fraudulent.",
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate CLI arguments after parsing."""
        self.policy_type = getattr(ns, "policy_type", "auto")
        self.fraud_percent = max(0, min(100, getattr(ns, "fraud_percent", 0)))

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario insurance-claim "
            "--count 30 "
            "--policy-type home "
            "--fraud-percent 5 "
            "--output-format yaml"
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
    _STATUS: list[str] = ["open", "investigating", "approved", "rejected"]
    _INCIDENTS: dict[str, list[str]] = {
        "auto": ["collision", "theft", "windshield damage"],
        "home": ["fire", "flood", "break-in"],
        "health": ["surgery", "emergency room visit", "routine check-up"],
    }

    def _random_incident(self) -> str:
        """Select a random incident based on policy type."""
        return random.choice(self._INCIDENTS.get(self.policy_type, ["other"]))

    def build_prompt(
        self, output_format: str, *, unique_id: str | None = None
    ) -> str:  # noqa: D401
        """
        Construct the full system-prompt string for the requested *output_format*.
        """
        claim_id = unique_id or str(uuid.uuid4())
        date_of_loss = date.today() - timedelta(days=random.randint(1, 365))
        status = random.choice(self._STATUS)
        fraudulent = random.random() < (self.fraud_percent / 100.0)

        base = (
            "You are an insurance adjuster generating REALISTIC BUT ENTIRELY "
            "FICTIONAL insurance claim records for demonstrations.\n\n"
            "## CLAIM OVERVIEW\n\n"
            f"Claim ID: {claim_id}\n"
            f"Policy Type: {self.policy_type}\n"
            f"Incident: {self._random_incident()}\n"
            f"Date of Loss: {date_of_loss.isoformat()}\n"
            f"Status: {status}\n"
        )

        if fraudulent:
            base += "This claim MAY BE FRAUDULENT - add subtle anomalies.\n"

        # The kernel will substitute {{index}} with an incremental int.
        base += (
            "\n## REQUIRED OUTPUT\n\n"
            "Provide a single claim document with realistic data fields.\n"
            f"Respond in {output_format.upper()} only - no commentary.\n"
            "Do NOT invent real PII. Use synthetic names and addresses.\n"
            "Use ISO-8601 dates.\n"
            "Index placeholder: {{index}}\n"
        )
        return base

    # ------------------------------------------------------------------ #
    # Post-processing & helpers                                          #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> str:  # noqa: D401
        """
        Optional hook - here we simply validate JSON/YAML is well-formed.
        """
        try:
            if output_format == "json":
                json.loads(raw)
            elif output_format == "yaml":
                yaml.safe_load(raw)
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Validation failed: %s", exc)
        return raw

    def get_system_description(self) -> str:
        """Short blurb used by the engine when describing this tool."""
        return "Generates synthetic insurance claim records."
