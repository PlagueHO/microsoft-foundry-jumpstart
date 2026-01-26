"""
Legal-Contract Prompt Builder
=============================

Scenario-specific implementation of :class:`data_generator.tool.DataGeneratorTool`
that creates realistic (but fully fictional) legal-contract documents.
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Any

import yaml  # needed for YAML post-processing

from ..tool import DataGeneratorTool

_logger = logging.getLogger(__name__)


class LegalContractTool(DataGeneratorTool):
    """Generate synthetic legal contracts."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "legal-contract"
    toolName: str = "LegalContract"

    # ------------------------------------------------------------------ #
    # Contract-specific settings                                         #
    # ------------------------------------------------------------------ #
    _CONTRACT_TYPES: list[str] = [
        "NDA",
        "Service Agreement",
        "Lease Agreement",
        "Employment Contract",
    ]
    _COMPLEXITY: list[str] = ["simple", "moderate", "complex"]

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(self) -> None:
        """Instantiate the tool with sensible defaults."""
        super().__init__()
        self.contract_type: str | None = None
        self.num_clauses: int = 5
        self.complexity: str = "moderate"

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--contract-type"],
                "kwargs": {
                    "choices": self._CONTRACT_TYPES,
                    "metavar": "TYPE",
                    "help": "Type of contract to generate.",
                },
            },
            {
                "flags": ["--num-clauses"],
                "kwargs": {
                    "type": int,
                    "default": 5,
                    "metavar": "N",
                    "help": "Approximate number of clauses per contract.",
                },
            },
            {
                "flags": ["--complexity"],
                "kwargs": {
                    "choices": self._COMPLEXITY,
                    "default": "moderate",
                    "help": "Legal language complexity.",
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate mandatory arguments after CLI parsing."""
        if ns.num_clauses <= 0:
            raise ValueError("--num-clauses must be positive.")
        # Persist for later use
        self.contract_type = ns.contract_type
        self.num_clauses = ns.num_clauses
        self.complexity = ns.complexity

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario legal-contract "
            "--contract-type NDA --num-clauses 7 "
            "--count 10 --output-format jsonl",
            "python -m generate_data "
            "--scenario legal-contract "
            '--contract-type "Service Agreement" --complexity complex '
            "--count 5 --output-format jsonl",
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:  # noqa: D401
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "txt"]

    # ------------------------------------------------------------------ #
    # Prompt helpers                                                     #
    # ------------------------------------------------------------------ #
    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Return the invariant part shared by all output formats."""
        contract_id = (
            unique_id or f"LC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        )
        effective = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return (
            f"Contract ID (immutable): {contract_id}\n"
            f"Contract Type: {self.contract_type or 'legal contract'}\n"
            f"Language Complexity: {self.complexity}\n"
            f"Clause Count (approx.): {self.num_clauses}\n"
            f"Effective Date: {effective}\n"
            "Use ISO-8601 dates and do NOT invent real PII.\n\n"
        )

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    def build_prompt(
        self,
        output_format: str,
        *,
        unique_id: str | None = None,
    ) -> str:
        """Construct the full system-prompt string (YAML/JSON/TXT)."""
        base = (
            "You are a helpful legal assistant creating REALISTIC BUT ENTIRELY "
            "FICTIONAL contracts for demonstrations.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
        )

        fmt = output_format.lower()
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
            "contract_id: (echo above)\n"
            "contract_type: (echo above)\n"
            "title: short descriptive title\n"
            "parties:\n"
            "  - Alpha Corp\n"
            "  - Beta Inc\n"
            "effective_date: ISO-8601\n"
            "termination_date: ISO-8601 (optional)\n"
            "governing_law: text\n"
            "clauses:\n"
            "  - clause_title: Confidentiality\n"
            "    clause_text: Both parties agree ...\n"
            "full_text: concatenated text of all clauses and metadata\n"
        )

    @staticmethod
    def _json_skeleton() -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return VALID JSON ONLY (no markdown fences).\n\n"
            "{\n"
            '  "contract_id": "(echo above)",\n'
            '  "contract_type": "(echo above)",\n'
            '  "title": "short descriptive title",\n'
            '  "parties": ["Alpha Corp", "Beta Inc"],\n'
            '  "effective_date": "ISO-8601",\n'
            '  "termination_date": "ISO-8601 (optional)",\n'
            '  "governing_law": "text",\n'
            '  "clauses": [\n'
            '    {\n'
            '      "clause_title": "Confidentiality",\n'
            '      "clause_text": "Both parties agree ..."\n'
            "    }\n"
            "  ],\n"
            '  "full_text": "concatenated text of all clauses and metadata"\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for free-form tools."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Contract ID: (echo above)\n"
            "Contract Type: (echo above)\n"
            "Title: short descriptive title\n"
            "Parties: Alpha Corp; Beta Inc\n"
            "Effective Date: ISO-8601\n"
            "Termination Date: ISO-8601 (optional)\n"
            "Governing Law: text\n"
            "Clauses:\n"
            "  - Confidentiality: Both parties agree ...\n"
            "Full Text: concatenated text\n"
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
        if fmt == "yaml" and ":" in raw and "\n" in raw:
            try:
                return yaml.safe_load(raw)
            except yaml.YAMLError:
                return raw
        # plain-text or unrecognized format
        return raw

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:  # noqa: D401
        """Return a short human-readable description of the tool."""
        return "Synthetic legal-contract data generator."
