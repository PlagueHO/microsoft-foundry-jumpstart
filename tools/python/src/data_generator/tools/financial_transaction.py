"""
Financial Transaction Data Generator.

This module provides a tool to generate synthetic financial transaction data
for testing and development purposes. Supports various output formats including
JSON, YAML, and text.
"""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import date, timedelta
from typing import Any

import yaml

from ..tool import DataGeneratorTool


class FinancialTransactionTool(DataGeneratorTool):
    """Generate synthetic bank-account statements with ≥50 transactions."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "financial-transaction"
    toolName: str = "FinancialTransaction"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(self, *, account_type: str | None = None) -> None:
        """Instantiate with optional *account_type* override."""
        super().__init__()
        self.account_type = account_type or "checking"
        self.transactions_max = 50
        self.fraud_percent = 0

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Define scenario-specific CLI flags."""
        return [
            {
                "flags": ["-a", "--account-type"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "checking",
                    "help": "Account type (checking, savings, credit).",
                },
            },
            {
                "flags": ["--transactions-max"],
                "kwargs": {
                    "required": False,
                    "metavar": "N",
                    "type": int,
                    "default": 50,
                    "help": "Minimum number of transactions per statement.",
                },
            },
            {
                "flags": ["--fraud-percent"],
                "kwargs": {
                    "required": False,
                    "metavar": "P",
                    "type": int,
                    "default": 0,
                    "help": (
                        "Percentage chance to include one subtle fraudulent transaction"
                    ),
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Persist CLI args onto the instance."""
        self.account_type = ns.account_type or self.account_type
        self.transactions_max = ns.transactions_max
        self.fraud_percent = max(0, min(100, ns.fraud_percent))

    def examples(self) -> list[str]:
        """Usage examples for help text."""
        return [
            "python -m data_generator "
            "--scenario financial-transaction "
            "--count 5 "
            "--account-type savings "
            "--transactions-max 75 "
            "--output-format json "
            "--out-dir ./data/financial"
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
    def _statement_period(self) -> tuple[str, str]:
        """Compute previous full-month period dates."""
        today = date.today()
        first_current = today.replace(day=1)
        last_prev = first_current - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        return first_prev.isoformat(), last_prev.isoformat()

    def _prompt_common(self, *, unique_id: str | None = None) -> dict[str, str]:
        """Return identifiers and period for the statement."""
        stmt_id = unique_id or str(uuid.uuid4())
        acct_id = str(random.randint(10**9, 10**10 - 1))
        start, end = self._statement_period()
        return {
            "statement_id": stmt_id,
            "account_id": acct_id,
            "account_type": self.account_type,
            "start_date": start,
            "end_date": end
        }

    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        """Assemble the full prompt for the desired format."""
        hdr = self._prompt_common(unique_id=unique_id)
        base = (
            "You are a banking data specialist creating realistic but entirely "
            "fictional account statements. No real PII.\n\n"
            f"Statement ID: {hdr['statement_id']}\n"
            f"Account ID: {hdr['account_id']} ({hdr['account_type']})\n"
            f"Period: {hdr['start_date']} - {hdr['end_date']}\n\n"
            f"Generate at least {self.transactions_max} transactions: dates, "
            f"descriptions, amounts, "
            "running balances; use ISO-8601 dates and two-decimal USD amounts.\n\n"
        )
        if self.fraud_percent > 0:
            base += (
                f"There is a {self.fraud_percent}% chance that one transaction "
                + "should be subtly fraudulent (e.g. small duplicate charge "
                + "or slight amount mismatch).\n\n"
            )
        if output_format == "yaml":
            return base + self._yaml_skeleton(hdr)
        if output_format == "json":
            return base + self._json_skeleton(hdr)
        return base + self._text_skeleton()

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    def _yaml_skeleton(self, hdr: dict[str, str]) -> str:
        """YAML schema instructions including echo fields."""
        return (
            "Return valid YAML only (no fences).\n\n"
            f"statement_id: {hdr['statement_id']}\n"
            f"account_id: {hdr['account_id']}\n"
            f"account_type: {hdr['account_type']}\n"
            f"start_date: {hdr['start_date']}\n"
            f"end_date: {hdr['end_date']}\n"
            "opening_balance: decimal number\n"
            "closing_balance: decimal number\n"
            "currency: USD\n"
            "transactions:\n"
            "  - tx_id: uuid\n"
            "    date: ISO 8601\n"
            "    description: text\n"
            "    amount: decimal (neg=debit, pos=credit)\n"
            "    balance_after: decimal\n"
            "    category: groceries|salary|utilities|other\n"
            f"# repeat for ≥{self.transactions_max} transactions\n"
        )

    def _json_skeleton(self, hdr: dict[str, str]) -> str:
        """JSON schema instructions including echo fields."""
        return (
            "Return valid JSON only (no fences).\n\n"
            "{\n"
            f'  "statement_id": "{hdr["statement_id"]}",\n'
            f'  "account_id": "{hdr["account_id"]}",\n'
            f'  "account_type": "{hdr["account_type"]}",\n'
            f'  "start_date": "{hdr["start_date"]}",\n'
            f'  "end_date": "{hdr["end_date"]}",\n'
            '  "opening_balance": 1234.56,\n'
            '  "closing_balance": 2345.67,\n'
            '  "currency": "USD",\n'
            '  "transactions": [\n'
            "    { \"tx_id\": \"uuid\", \"date\": \"ISO\", \"description\": \"text\", "
            "\"amount\": -12.34, \"balance_after\": 1222.22, "
            "\"category\": \"groceries\" }\n"
            f"    // ... ≥{self.transactions_max} entries ...\n"
            "  ]\n"
            "}\n"
        )

    def _text_skeleton(self) -> str:
        """Plain-text layout guidelines."""
        return (
            "Return plain text without any YAML/JSON markers.\n\n"
            "Opening Balance: 1234.56 USD\n"
            "Closing Balance: 2345.67 USD\n\n"
            "Transactions:\n"
            "date       | description         | amount   | balance_after | category\n"
            "YYYY-MM-DD | Grocery Purchase    | -45.67   | 1188.89       | groceries\n"
            f"# ... ≥{self.transactions_max} rows ...\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:
        """Deserialize based on output_format; fallback to raw text on failure."""
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
        # text or other formats
        return raw

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Describe this tool’s context."""
        return f"Financial transactions for {self.account_type} accounts"
